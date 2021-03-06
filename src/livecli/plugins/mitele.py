from __future__ import print_function

import re

from livecli import NoStreamsError
from livecli.compat import urljoin
from livecli.plugin import Plugin
from livecli.plugin.api import http
from livecli.plugin.api import useragents
from livecli.plugin.api import validate
from livecli.stream import HLSStream
from livecli.utils import parse_json

__livecli_docs__ = {
    "domains": [
        "mitele.es",
    ],
    "geo_blocked": [
        "ES",
    ],
    "notes": "",
    "live": True,
    "vod": False,
    "last_update": "2018-01-06",
}


class Mitele(Plugin):
    _url_re = re.compile(r"https?://(?:www\.)?mitele\.es/directo/(?P<channel>\w+)")
    _suffix_re = re.compile(r"""acl=(?P<path>[^"'*]+)""")

    livehlsdai = "https://livehlsdai-i.akamaihd.net"
    mdslivehls = "https://mdslivehls-i.akamaihd.net"

    _channel_domains = {
        "bemad": mdslivehls,
        "boing": mdslivehls,
        "cuatro": livehlsdai,
        "divinity": mdslivehls,
        "energy": mdslivehls,
        "fdf": mdslivehls,
        "telecinco": livehlsdai,
    }

    pdata_url = "https://indalo.mediaset.es/mmc-player/api/mmc/v1/{channel}/live/flash.json"
    gate_url = "https://gatekeeper.mediaset.es"

    pdata_schema = validate.Schema(
        validate.all(
            {
                "locations": [{
                    "gcp": validate.text,
                    "ogn": validate.text,
                }],
            },
            validate.get("locations"),
            validate.get(0),
        )
    )

    def __init__(self, url):
        super(Mitele, self).__init__(url)
        self.headers = {
            "User-Agent": useragents.FIREFOX,
            "Referer": self.url
        }

    @classmethod
    def can_handle_url(cls, url):
        m = cls._url_re.match(url)
        return m and m.group("channel") in cls._channel_domains.keys()

    def get_pdata(self, channel):
        """
        Get the params for the post request
        :param channel: channel name
        :return: "gcp" and "ogn"
        """
        res = http.get(self.pdata_url.format(channel=channel))
        return parse_json(res.text, schema=self.pdata_schema)

    def create_hls_url(self, suffix):
        """
        creates a valid hls_url
        :param suffix: url session params
        :return: hls_url
        """
        m = self._suffix_re.search(suffix)
        if not m:
            return
        self.logger.debug("create hls_url from suffix")

        channel = self._url_re.match(self.url).group("channel")
        domain = self._channel_domains[channel]
        path = m.group("path")
        path_suffix = "master.m3u8?{suffix}".format(suffix=suffix)

        hls_url = urljoin(domain, path)
        hls_url = urljoin(hls_url, path_suffix)
        return hls_url

    def get_stream_url(self, data):
        """
        Get the hls_url from the post request
        :param data: dict with "gcp" and "ogn"
        :return: hls_url
        """
        try:
            res = http.post(self.gate_url, headers=self.headers, data=data)
        except Exception as e:
            if "403" in str(e):
                self.logger.error("This Video is Not Available in Your Country.")
            raise NoStreamsError(self.url)

        r_data = parse_json(res.text)
        hls_url = r_data.get("stream")
        suffix = r_data.get("suffix")

        if hls_url is None and suffix:
            hls_url = self.create_hls_url(suffix)
        return hls_url

    def _get_streams(self):
        channel = self._url_re.match(self.url).group("channel")

        pdata = self.get_pdata(channel)
        hls_url = self.get_stream_url(pdata)

        if hls_url:
            self.logger.debug("HLS URL: {0}".format(hls_url))
            for s in HLSStream.parse_variant_playlist(self.session, hls_url, headers=self.headers).items():
                yield s


__plugin__ = Mitele
