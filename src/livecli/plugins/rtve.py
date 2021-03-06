import base64
import re
from functools import partial


from livecli.compat import crypto_Blowfish
from livecli.compat import bytes, is_py3
from livecli.plugin import Plugin, PluginOptions
from livecli.plugin.api import http
from livecli.plugin.api import useragents
from livecli.plugin.api import validate
from livecli.stream import HLSStream
from livecli.stream import HTTPStream
from livecli.stream.ffmpegmux import MuxedStream
from livecli.utils import parse_xml

__livecli_docs__ = {
    "domains": [
        "rtve.es",
    ],
    "geo_blocked": [],
    "notes": "",
    "live": True,
    "vod": False,
    "last_update": "2017-02-27",
}


class ZTNRClient(object):
    base_url = "http://ztnr.rtve.es/ztnr/res/"
    block_size = 16

    def __init__(self, key):
        self.cipher = crypto_Blowfish.new(key, crypto_Blowfish.MODE_ECB)

    @classmethod
    def pad(cls, data):
        n = cls.block_size - len(data) % cls.block_size
        return data + bytes(chr(cls.block_size - len(data) % cls.block_size), "utf8") * n

    @staticmethod
    def unpad(data):
        if is_py3:
            return data[0:-data[-1]]
        else:
            return data[0:-ord(data[-1])]

    def encrypt(self, data):
        return base64.b64encode(self.cipher.encrypt(self.pad(bytes(data, "utf-8"))), altchars=b"-_").decode("ascii")

    def decrypt(self, data):
        return self.unpad(self.cipher.decrypt(base64.b64decode(data, altchars=b"-_")))

    def request(self, data, *args, **kwargs):
        res = http.get(self.base_url + self.encrypt(data), *args, **kwargs)
        return self.decrypt(res.content)

    def get_cdn_list(self, vid, manager="apedemak", vtype="video", lang="es", schema=None):
        data = self.request("{id}_{manager}_{type}_{lang}".format(id=vid, manager=manager, type=vtype, lang=lang))
        if schema:
            return schema.validate(data)
        else:
            return data


class Rtve(Plugin):
    secret_key = base64.b64decode("eWVMJmRhRDM=")
    content_id_re = re.compile(r'data-id\s*=\s*"(\d+)"')
    url_re = re.compile(r"""
        https?://(?:www\.)?rtve\.es/(?:directo|noticias|television|deportes|alacarta|drmn)/.*?/?
    """, re.VERBOSE)
    cdn_schema = validate.Schema(
        validate.transform(partial(parse_xml, invalid_char_entities=True)),
        validate.xml_findall(".//preset"),
        [
            validate.union({
                "quality": validate.all(validate.getattr("attrib"),
                                        validate.get("type")),
                "urls": validate.all(
                    validate.xml_findall(".//url"),
                    [validate.getattr("text")]
                )
            })
        ]
    )
    subtitles_api = "http://www.rtve.es/api/videos/{id}/subtitulos.json"
    subtitles_schema = validate.Schema({
        "page": {
            "items": [{
                "src": validate.url(),
                "lang": validate.text
            }]
        }
    },
        validate.get("page"),
        validate.get("items"))
    video_api = "http://www.rtve.es/api/videos/{id}.json"
    video_schema = validate.Schema({
        "page": {
            "items": [{
                "qualities": [{
                    "preset": validate.text,
                    "height": int
                }]
            }]
        }
    },
        validate.get("page"),
        validate.get("items"),
        validate.get(0))
    options = PluginOptions({
        "mux_subtitles": False
    })

    @classmethod
    def can_handle_url(cls, url):
        return cls.url_re.match(url) is not None

    def __init__(self, url):
        Plugin.__init__(self, url)
        self.zclient = ZTNRClient(self.secret_key)
        http.headers = {"User-Agent": useragents.SAFARI_8}

    def _get_content_id(self):
        res = http.get(self.url)
        m = self.content_id_re.search(res.text)
        return m and int(m.group(1))

    def _get_subtitles(self, content_id):
        res = http.get(self.subtitles_api.format(id=content_id))
        return http.json(res, schema=self.subtitles_schema)

    def _get_quality_map(self, content_id):
        res = http.get(self.video_api.format(id=content_id))
        data = http.json(res, schema=self.video_schema)
        qmap = {}
        for item in data["qualities"]:
            qname = {"MED": "Media", "HIGH": "Alta", "ORIGINAL": "Original"}.get(item["preset"], item["preset"])
            qmap[qname] = u"{0}p".format(item["height"])
        return qmap

    def _get_streams(self):
        streams = []
        content_id = self._get_content_id()
        if content_id:
            self.logger.debug("Found content with id: {0}", content_id)
            stream_data = self.zclient.get_cdn_list(content_id, schema=self.cdn_schema)
            quality_map = None

            for stream in stream_data:
                for url in stream["urls"]:
                    if url.endswith("m3u8"):
                        try:
                            streams.extend(HLSStream.parse_variant_playlist(self.session, url).items())
                        except (IOError, OSError):
                            self.logger.debug("Failed to load m3u8 url: {0}", url)
                    elif ((url.endswith("mp4") or url.endswith("mov") or url.endswith("avi")) and
                            http.head(url, raise_for_status=False).status_code == 200):
                        if quality_map is None:  # only make the request when it is necessary
                            quality_map = self._get_quality_map(content_id)
                        # rename the HTTP sources to match the HLS sources
                        quality = quality_map.get(stream["quality"], stream["quality"])
                        streams.append((quality, HTTPStream(self.session, url)))

            subtitles = None
            if self.get_option("mux_subtitles"):
                subtitles = self._get_subtitles(content_id)
            if subtitles:
                substreams = {}
                for i, subtitle in enumerate(subtitles):
                    substreams[subtitle["lang"]] = HTTPStream(self.session, subtitle["src"])

                for q, s in streams:
                    yield q, MuxedStream(self.session, s, subtitles=substreams)
            else:
                for s in streams:
                    yield s


__plugin__ = Rtve
