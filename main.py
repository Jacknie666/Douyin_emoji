import requests
from bs4 import BeautifulSoup
import zipfile
import re
from PIL import Image, ImageSequence, UnidentifiedImageError
import io
import os
from urllib.parse import urlparse
import concurrent.futures  # 用于多线程

# --- 全局配置 (可调整) ---
HTML_CONTENT_FILE = None  # "your_emoticons_page.html" # 如果从文件读取HTML，请设置此路径
MAX_EMOTICONS_TO_DOWNLOAD = 0  # 下载表情的最大数量 (0 表示下载所有找到的表情)
MAX_DOWNLOAD_WORKERS = 10  # 并发下载线程数
MAX_CONVERSION_WORKERS = os.cpu_count() or 4  # 并发转换线程数 (使用CPU核心数或默认4)
REQUEST_TIMEOUT = 20  # 网络请求超时时间 (秒)
ZIP_FILENAME = "DOUYIN_emoji.zip"  # 输出的ZIP文件名
GIF_LOOP_COUNT = 0  # GIF循环次数 (0 代表无限循环)
GIF_DEFAULT_FRAME_DURATION = 80  # ms (毫秒，约12.5 FPS), 可以根据表情包特性调整
GIF_MIN_FRAME_DURATION = 20  # ms (毫秒，GIF规范通常要求至少2厘秒，即20ms)
GIF_OPTIMIZE = True  # 是否优化GIF以减小体积 (可能会稍微慢一些)
GIF_QUANTIZE_COLORS = 256  # GIF调色板颜色数量 (0表示不量化，但通常建议量化以获得更好的兼容性和更小的文件)
GIF_QUANTIZE_METHOD = Image.Quantize.FASTOCTREE  # 调色板量化方法: MEDIANCUT, MAXCOVERAGE, FASTOCTREE
GIF_DITHER_METHOD = Image.Dither.FLOYDSTEINBERG  # 抖动方法: None, FLOYDSTEINBERG (用于改善颜色过渡)

# demo展示HTML内容
html_content = """
<div class="JQ9dA4iS">
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="u90oxwn" data-popupid="u90oxwn">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oEWAAufhdIAnENBIRX5lWfQAfMke8XGgNAQfHQ~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=w9j65%2B%2BD25T5gLgAF6G5i5AHypU%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="17e4eh5" data-popupid="17e4eh5">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oUCCAhRIeNfILfLG9zQAizDM2jAeQd9SACJI9G~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=Uvdpvu0CyWj0l0ziwEFyjebj7qw%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="sjom4gc" data-popupid="sjom4gc">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/owQR6Af6NKQAOqxByogpIMFE1CAIAoSFDfAVCn~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=L1QrJKqxTO6agO255xE20oky1PU%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="vohg0xg" data-popupid="vohg0xg">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oEQZBehzQAcMEhhlI3AlABBeAjL3ZGeyFAXG9I~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=fHFqLU4y7P76aduq98R9nyNNvhk%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="sjbb64x" data-popupid="sjbb64x">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/okCdAlVQfFCAnyEAIoEDlgfgQAz4gs2wACAGxx~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=0Zh9c5sOdgDhHlduWzKUB4eqRhA%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="uw22bdw" data-popupid="uw22bdw">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ogAiFjAMitQ8anAEXxPAmjBAkIsI2CzoEjN1N~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=wK3gTGiC8z6U5WMEYUM7Q0qaxDQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="uq35oqu" data-popupid="uq35oqu">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oAw93iBYGB0AGYZVSQAjA5uGEfjxDPgigUIACA~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=fhGuinkhFRyG6XvcU4tpBhadOk0%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="mol0it8" data-popupid="mol0it8">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o8JaGLGVjlBvzIAXWEIE09EBTAsA65AeiQe3eB~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=jIBHsVMyio%2BEFRWlfOpZWp9xiMM%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="3q68efq" data-popupid="3q68efq">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oIBLxBXfrIMo53ADXeAA8qQPgfQxGBeCIAv60I~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=j8GnVV1x19Nizu9MwtRRTV7qwOk%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="83tbs60" data-popupid="83tbs60">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oISyiqjIQoxYAEHC0AIB9UinZ5AEBgfFBtAxBA~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=Z2ZRURm3zlAumOEfFxyjHwkMXBg%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="n2xfpi1" data-popupid="n2xfpi1">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oUl8Q3ENBAAgHOjIAIGeeAoB5hfG3LrXKGTSIl~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=TCnDh3eBOHvuCTij%2B83wUkxnbD8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="1ktoo4y" data-popupid="1ktoo4y">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oU0ABJH48BSEeAiYxADIZvDAAAZjQWPA1GhBiX~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=orAdvN1bCgYyxH3nxLhEneauTjo%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="t7lwf9q" data-popupid="t7lwf9q">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oEFTOArPfBqLBBmAEpNiHjJEGZefQnYAl20AID~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=%2BeHAH2a2Zfgyo69jMLkS23jGVe4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="nsg2218" data-popupid="nsg2218">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oMZElmEQBSAiDiv5DoYhzevPAlBTgBAIDAZzrr~tplv-0wx4r9yasq-awebp-resize:540:540.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=2bK2M0Nol2cycUkAE3QeE5yizJ8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="zfh9zoa" data-popupid="zfh9zoa">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/osGiAIeAqQdf5LuWLQyeHbbVLxAYQMA0efIOGE~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=%2FsA2cy7zkmey8Z6Hemnd11fzX7s%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="x6rin8a" data-popupid="x6rin8a">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/osiGOAYZEAAfyIAdA0AQMA7KBBius9DBvoAQE2~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=IB9Cpu%2BkDXn1%2BqkP2rNzVKiyfh8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="axm76p7" data-popupid="axm76p7">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o0xCwFAxA7MfDq6zAn27A0CoDAEyIAeYDKr6Eg~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=A0ukU5mTRN4bqXLogfd8eeSCeXA%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="7qyu6u9" data-popupid="7qyu6u9">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/okA3YjeiMgMUQMzCB9XAE8jnhE8DPABQQfAelh~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=NJlrexWP%2FanULEUb347KMr84H8w%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="p9evifq" data-popupid="p9evifq">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oMeIACeYGAemfCgJeiewAAbx4LnAeAh5fyAUDgu~tplv-0wx4r9yasq-awebp-resize:540:540.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=4KMC3toBD5Ed7VGLuThArnSHSZw%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="t3etvqo" data-popupid="t3etvqo">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ogG88geoAe9KfLAW9fWQGHQWIfQEqIhAMQHAYG~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=iP4fzcBH0P9g5Nf4xc0GxPuCvMM%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="knd729a" data-popupid="knd729a">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ocIBnfA9N5EjyCHQmnoA4tAAiDCA8oAEAgfixd~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=pWwZkgtk%2BNRqivQIBtXLf9yK%2BUU%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="awc0rv6" data-popupid="awc0rv6">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oYedfAaGQElv7G3LIAA5ABI9lBLreaXA6jQ1BV~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=pKiwkAcgZXG8EjeN6DuoYUhGogk%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="uzt63rf" data-popupid="uzt63rf">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oIA3iIzEA8xrAILEiCFoA3ADgyCrAAjOf9Nyf5~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=uKxDgxFxpqFXqIuaEw%2B6Ed9pjHo%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="0zib6bb" data-popupid="0zib6bb">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o4sI6AGB0BB8TEciiAA4zAEoZgD3fGFQ0YIGAw~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=jzqzLi3D8%2FaStajMZdjyoRhTqqk%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="c7r1zb2" data-popupid="c7r1zb2">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o0AAfQAdFUgDA25eSrIsILiLGCEGJACMMIeBfp~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=irjabIg4vdUL9%2BWEizgr33nm%2BE0%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="j5kflcv" data-popupid="j5kflcv">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/ies.fe.effect/f01e4f6eb2395710aeaa1a423dbb4b23~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=A8EcdUpibsxfqR6iv%2F5F0AU6CHQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="glcwsvi" data-popupid="glcwsvi">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/3ba24f70edd04c7d9638839e23cf056f~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=KnNsfJG3bRZKwXL0i%2B9lPsqeHg4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="tr2iaxq" data-popupid="tr2iaxq">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o8RJEEydBGBSifADAxLgBjOAAl2AeEWDILemHI~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=b%2FFAU6kqJIStiMnL66GopbxgoZo%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="6tdswba" data-popupid="6tdswba">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/ies.fe.effect/52c6d586c3c5e680b7a496f871a45396~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=G2jsUqK%2FPCzUvHAR3o87XUH%2B7WQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="zf9dt3d" data-popupid="zf9dt3d">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/850f998bc0bb4eb28bbe14396d1d699d~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=XYsGwSJ3%2FkdmP0i%2Fn7ZeX7bpmvM%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="p2hxxpv" data-popupid="p2hxxpv">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/ies.fe.effect/b2129852460c401feb95f1c982f89a0e~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=cawTL88CHSoyPMvMyEBxIJNP%2F%2Fo%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="twrid92" data-popupid="twrid92">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ooDCAs4hwEgQeIUAdAGfeIZn0QeGIWLAAG8LoT~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=%2FSzlIky0YxgoaFulKs%2BlIlgHoH8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="itia096" data-popupid="itia096">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/4d83c03ac227413b976ff04eb3a3fe92~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=RBJtEkQgscZbukRKzqzvQ2u3z5k%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="9sg9s1q" data-popupid="9sg9s1q">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o0FLsACoBACJAODAEqehAxECNMGfIC5AyU3gED~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=RYX3qD23YQ6qPWwbS20Q95OTGfI%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="sbxvfcx" data-popupid="sbxvfcx">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o8btJJ4NHCA8XQeIAQ8AaAABzSKgXmeinyx5DA~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=zNgyawWd9MhkvMAJAHXQ1xcxvYQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="10g32ja" data-popupid="10g32ja">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oAQMstd0NBNwBAAyWSApPJEAiM6iZIzAgInCj~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=SKtP4ePpgTvhAgjaby39kG2ndAQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="gll5hih" data-popupid="gll5hih">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/16970f5e40084b1d802b1941b9d05169~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=uU4320A9BJbpD2xrQRejL8dTIs4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="1ae6gt6" data-popupid="1ae6gt6">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/osnANfWb2CTIzAFxtAGQ1u3AAiyLgGfEHdbDEw~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=XyPDIswupV9ueILwfeoTXoA3WtI%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="lx2a562" data-popupid="lx2a562">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oUQo6PeEApjUAIqEsEFPB7DDA1EFABs7fd0lf1~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=4tC7bKNep25XJOLOMHDc9mth14c%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="qjb47b9" data-popupid="qjb47b9">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o83GTwwIAej7AIlE3ELQBTAGAfEFABigeJDl6y~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=1Cej0Lkg7oFl2UomJlK%2B1bLDMw4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="vgj5zx0" data-popupid="vgj5zx0">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-0813/oAiP9nAVTB2EAtTPAAIAlkYfsfxggFEDA2NCx7~tplv-0wx4r9yasq-webp-resize:1080:1063.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=g8XsGqdz4QQDylgzE0kdlhYdOSo%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="3hk6vzx" data-popupid="3hk6vzx">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/okcIfBD7B0DBTFjfPSVfJAalAEX3EE8IAAu6E0~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=AsWYmsC05k%2BWACFcRZWX1pQVKiA%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="f9uej7n" data-popupid="f9uej7n">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o8N6jC4EA2xDAQNIUCFnAfGDgyDyAA3ifX3yr6~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=9PcqqqLd%2BuJ3ZV0bVLSMmIDvZkc%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="d06ohfj" data-popupid="d06ohfj">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oMELIABAjt6FB4DQCFAcffnyGjsleEAAGo2HEt~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=g4oOOVhC2C8YWJ5AxfaShSrbxwg%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="bpd6msa" data-popupid="bpd6msa">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ocvwMiLZiIAEQqBq9PvewAqAYAIo0BBzAAHqB2~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=W%2FPIcXhBwLDWEaFFaJHG6F7WZ4A%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="1v8bqm2" data-popupid="1v8bqm2">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/ies.fe.effect/ffb4750a297e8bedd5243b9c246a6466~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=GFCg0wqMoxdNFEsqKY1Dn6MHNLg%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="12vb9em" data-popupid="12vb9em">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/32562fa554c24294ae02ad0dc9c2b098~tplv-0wx4r9yasq-webp-resize:956:876.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=bFxSl7sisZjLwS2LqdnPQXp5kjM%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="bs0i8hv" data-popupid="bs0i8hv">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ocOgAIzIqasBOBjBQcBDQfiEiZAYCAV5kvi3AE~tplv-0wx4r9yasq-webp-resize:593:594.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=vPdyRw5cypdAp3NU6FUnHF6tpHQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="8wdchxt" data-popupid="8wdchxt">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/douyin-user-image-file/01c8afd2e004861c52c4e3a521892cf9~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=2fx%2BmFuLGJjL%2BKmKv2ifhkdTFWg%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="0cdoksl" data-popupid="0cdoksl">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/ies.fe.effect/c919c146e805b139d3eda36a7ae2cb8e~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=cNat2lvZnXu65lEtUHdTP4DkjA0%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="vw0muqw" data-popupid="vw0muqw">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/ab4d28c114a24270bb18bcdbd625c2a8~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=btl4KgByE1NYJ5zH%2Fjc%2FgmeI0Ms%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="w8dyng6" data-popupid="w8dyng6">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/ies.fe.effect/ca90469f91a2a6b0f172abc4253a9c16~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=5jO1PYSgqVeLJ2T8Uh18%2FTXj0nc%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="i5xxtuy" data-popupid="i5xxtuy">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/b1cb6d89af294e40abf4254926371724~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=9chbxVq0EFL7a3s2diMF5j70Rp8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="n99zb9c" data-popupid="n99zb9c">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/8c5bd920b45240ba92aa83fbc398b773~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=CAoomNaXLbW%2F9uCnutB1wHKURx8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="s8s7i8i" data-popupid="s8s7i8i">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/owAjewEDNAr47ga7lxde20AEDfB2FBA6TEAPbI~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=c8yaf5eAc1HzLaQ5V5Bl5puMDbA%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="awbxl3f" data-popupid="awbxl3f">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/2fafe34226a442c1bb406d872d5b0656~tplv-0wx4r9yasq-webp-resize:894:797.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=5mdOgHaMNurz5LHzV4aWgxdS9Bc%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="sav1im3" data-popupid="sav1im3">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/55ef783bb3b54c0380c1aa5aa1be0193~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=No4amLXGK80eIrJe0YrmQsTahpM%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="b9l07qz" data-popupid="b9l07qz">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/ies.fe.effect/4455503aa4af8ca746d558d96678f687~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=1j8TA%2BuEtt6eTErJuEKgMpBltP0%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="1vofdku" data-popupid="1vofdku">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o8DBqEIJoBGAjbAfUSApLSGBepaAAOIlSeEJ1n~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=hgCurhd1Pt%2FDYHpTE%2BaQu5Y87ww%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="wvyryu2" data-popupid="wvyryu2">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/ies.fe.effect/6aa5ce3f89ac581a3569b93b662f7d0e~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=5dfWFcz4TNOxT3qgfR6kXVQ3z4o%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="7t98vs4" data-popupid="7t98vs4">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ogIAdmnyRCvARgxZ9xQADFEAjeDBQbAVPfKFMD~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=QGnI0le%2BYNJs1%2Bpjjgml7UaExhU%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="970h9vj" data-popupid="970h9vj">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oUPHikZstYgysIgAbcAIB1JMCiAAwBGiIEuAX~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=IkonwApSptUZOUxv0gX9NnQpF6w%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="g8kmvr6" data-popupid="g8kmvr6">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-i-0813/oYZAAQmBhEByiU1EAVobAgwNPoVIAPiIDgkRA~tplv-0wx4r9yasq-webp-resize:1920:1848.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=B4voHq3geS6RTBOLAtEzk9bj1ig%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="8thnkuz" data-popupid="8thnkuz">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o4IyQAAAxfdOAOnmzeBBbj8HG9SyzDAgN5X3C3~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=N74b%2FXejBMyl87K5ZLC%2BAkSjzlY%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="zbm2prn" data-popupid="zbm2prn">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oY3uYAA7zCggJiDQB1iiQzBHZyAYn8AIEaftGF~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=I19pNaljgVEcLzgr%2Fptci6Ogfhg%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="qugg9go" data-popupid="qugg9go">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/2206835ba3214d2ea7619e0726840f7d~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=7UL3Afx1zyEijsuCWGUWEaN2Vx0%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="3vfcn1a" data-popupid="3vfcn1a">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/17d72f1308954b0095b98320b36d15c9~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=3InmINifRjlZvAtW51fKZw%2FKuts%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="8y114xs" data-popupid="8y114xs">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/3702de90ca0b4c7a8e28bb1542c25a71~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=1iesj%2BbeNONHQxoemZTwFItNkBY%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="pq61ep0" data-popupid="pq61ep0">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ooyGCuyEATxzAIJE6CFnArBDgiCvAAaIfqRyfy~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=OpCWpE5NNGXFHTKpnGKHbGGXAZ4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="5o07roc" data-popupid="5o07roc">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/douyin-user-file/1a02480a38fea37fff49fa8f538e6bad~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=3m5NXRrPRJa%2B4AkIT2%2FqETvZofM%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="mpo6zh0" data-popupid="mpo6zh0">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oMDx8DfgA4MgMFAlE50EBZGKEfQBEIxAjtDAIe~tplv-0wx4r9yasq-webp-resize:955:883.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=%2FyaEz0NclESRvCO81bGyI%2FKMYfI%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="exbe9u2" data-popupid="exbe9u2">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ogArAbOenCBVeAFLe8DbNdE5eIIIFFgAH6GP8D~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=M5UBROlZXmfmUhDKbXICjnfKiAw%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="7xyu5pu" data-popupid="7xyu5pu">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/okRW6hgkThANFAOlAlAPIbEdtfyAUCACjzAxHf~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=wEfyGfsLEWoQdS1TXOb4w9a1nMo%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="we2sr83" data-popupid="we2sr83">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/ies.fe.effect/516fad67cf31035a38c83bcda50e07fc~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=oHVNZRXGNhCF1n0qiJ2%2BDPh9ejw%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="64mr2q0" data-popupid="64mr2q0">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/ies.fe.effect/aafa7524583861f64bb3c7589755560c~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=DsNGBwBndLhy8x51cALHTzS4MC4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="20yrdv8" data-popupid="20yrdv8">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-image-file/0d337230e747f64169c6647ffe20cf7b~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=8ug8DZDHAJJx7%2BHcAQiF2zxpHE8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="nsjc2rq" data-popupid="nsjc2rq">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/douyin-user-image-file/8c4e3619d4370a315d8330d35fc64fb7~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=nF9%2BEutyPMULLlQ7vSxp7RMhJw0%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="ot0g9sq" data-popupid="ot0g9sq">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-image-file/03dcce9e925b18e50436f4317e238531~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=QnGFZMtWGKO6rThO04pL8arGlLI%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="ynp9u03" data-popupid="ynp9u03">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oIRYApbnNIOcxjmyzj9qAHYoeCpAqD6AeAAUQg~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=y%2F0F6TPPWcrnT0GbZnNZwLizLjU%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="2dfusk7" data-popupid="2dfusk7">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/187da9c7a1a04baca99bcaef95bd098b~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=t%2B18hwNvc2%2F%2FVyPHXHO%2FnJ943%2FI%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="o7jtmpx" data-popupid="o7jtmpx">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oIfNEFjDl5DxfjNEV7F71EAvB8AyIAEseRAGsB~tplv-0wx4r9yasq-webp-resize:1079:1124.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=VUUStFj7iiezFwA6JzxobWhATDY%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="tfkjixv" data-popupid="tfkjixv">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-image-file/fe656c5c5ad5732df025478ed2e61134~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=vHWW3kvLbW2Vy9yMqTqYzgck6mQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="ln4ps0j" data-popupid="ln4ps0j">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-image-file/33279dc99fb25c82f6ac8d1c0354c4ae~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=socf3UUK9%2FOJBDMn%2FelGNgCtJ98%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="gttr5tj" data-popupid="gttr5tj">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ocASsFlMBICxEQ6mARiABzYMHBf5zAAEiLQxZS~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=yds1UY%2Bi3NjWN4zIC3IfAu1ebH8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="12qlmcb" data-popupid="12qlmcb">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oUIuXAA4MDBQG0PfEwFEAlD6lfBj3oAQI2fOE7~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=4VPvfBrglluhQPbd2A5lhC4C1G4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="jj5ezbm" data-popupid="jj5ezbm">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/0a8c5056629f4256a79d9c9ae38dbe3f~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=BZt%2B76laXnwm2FzkP3G%2FnN1i%2FUM%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="wjp1xos" data-popupid="wjp1xos">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/owaHMQOj5Q0MlFrBIN4AkvGNLjeABEeAJgfnAv~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=eh2R0myuPszuAnqx8XSTTkSM8zE%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="hu9my3u" data-popupid="hu9my3u">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oknKxmfNmENAyAAUbCCegA5DIwnA5sAtbgbklY~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=gNCPTdnW%2Bon3sjScQlB%2BXhDFrS4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="ac5vqo5" data-popupid="ac5vqo5">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-i-0813c001/owMajqSEAY9IAQbIECFmAiDDgKNfAACUfUbAap~tplv-0wx4r9yasq-webp-resize:1440:1440.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=nggKpGEV%2F1r5vXkrQRghQnYZNRA%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="rw3wyx6" data-popupid="rw3wyx6">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-0813c001/o8I9CCmAq3KM5uACDAEoDgFCOAACggfeEoAAUK~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=S6DBwoRFJW9MXmd7vWQI9xLSObU%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="1aq1wp0" data-popupid="1aq1wp0">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-i-0813/osfnAtSEUhE2bAKmA9AI9RHFjfBOkEANADQCgg~tplv-0wx4r9yasq-webp-resize:1440:1440.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=cOtEJp8F0V38sZJH309iHDvpHkI%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="v3rpstz" data-popupid="v3rpstz">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/douyin-user-file/457b27788e63492082ffda612f807f80~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=BfYeBLZtVpwSCVozWYL1mvf5jLY%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="gq83hw5" data-popupid="gq83hw5">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oUWyREADgiACF0IFfAmxAAAiI2EdigQ1iQAEeD~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=UTcuc71HLtxOn%2FRN33aeGkcAKrc%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="m51k3o0" data-popupid="m51k3o0">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oMrHoXMVMWE9pQAfIeQIpSRGrAfASeAuey8QQC~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=JlVEud%2BnqUHQOQBuqOkJXK5UccU%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="2iolx9z" data-popupid="2iolx9z">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/douyin-user-image-file/c750b73d931176b685903662b4ece086~tplv-0wx4r9yasq-webp-resize:1080:1063.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=RqT0nmh8pEl1lgp%2BATVq97ujBB0%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="8kelimt" data-popupid="8kelimt">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oIbvgLIhheGIMzA3f4HseAu0ZPA7eYTVnAgADC~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=pQyJLx8M4C7cygUAe1L9WDpGZeM%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="vwd9rvu" data-popupid="vwd9rvu">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-i-0813c001/oE4vHAIGZIeD4hgLIAAfcAQEDCWzesdAI2gfGv~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=DTIqr4bTXX9TLmHDXeuMgd9OXO8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="5fvy6zo" data-popupid="5fvy6zo">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oQX6MyAfEExiroAAjMmySDzCUImzCcAfgAnFBx~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=OLhSGFyerBKXKmSFQj%2FKc1aXxvc%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="5k6xajo" data-popupid="5k6xajo">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ocAAUF6ZWVtZDh5AxfPCInyfgCErABAIGmYSEm~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=EhoovAJTtj696Qq8EicQ%2BI0WkB0%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="a0cg98r" data-popupid="a0cg98r">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/cc1878353fcc452a94991bfe6fc46b72~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=YZ3phgUBW%2FWlwvV%2FmcDBbLFz0Uc%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="ngcjq7n" data-popupid="ngcjq7n">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/douyin-user-image-file/522f780986b622487fed4bff2ac16d2f~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=C%2FKKmbG%2F%2B52kggM9uubxMdECH2Q%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="2jbniyt" data-popupid="2jbniyt">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oMAqlmRfYzibBBAvBHB25Fi2As4OQAzE42wAIZ~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=rBaWcTwLlLK4D2gVqgzOAYBfeds%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="fccp0p0" data-popupid="fccp0p0">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oAAfAb8nnAHl8AWymjDMZxIc8CCQMeQghxxmjA~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=AyiDclBWuZcPTKgLEa2l7UPrAc4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="1qpwmgr" data-popupid="1qpwmgr">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/8a390c7aa4b4444e8711f3b1c53c3717~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=0lxmi77FqqDSwci8j9uwGbZKq4k%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="relx92r" data-popupid="relx92r">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ogvMEiVAQT4XfDeBuAhI406Ajcf9MBAEl8kQya~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=zMuNL8s%2BPd2n%2FpHsk5B5qUBBpn8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="3p6iq0r" data-popupid="3p6iq0r">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oQQxaDmAhLOxfPGEDAIusgFERAACLgftELyAcR~tplv-0wx4r9yasq-webp-resize:1116:728.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=G8hha4O7BiN17ji%2Fa%2FE0mkwVlD4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="x4vwcuu" data-popupid="x4vwcuu">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o0WiufQAQ8GLYIhCHfMcqfeUAWGtEQAgNAtzgf~tplv-0wx4r9yasq-webp-resize:540:537.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=T2bs35GHnJ0a52w1lSnDvzsKLY4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="n16mrl8" data-popupid="n16mrl8">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oQ9QO28HAAhZvyBzYGkBApzNIiIaEAilABAMfB~tplv-0wx4r9yasq-awebp-resize:800:566.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=EkXRrPf%2BIz18r0NhzDv4X2cuk5M%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="jthcq0v" data-popupid="jthcq0v">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/o4QjpEMBfX4DDA0nDBIyk5FDlAAEuAflEelAkk~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=5YOgpD02t5GrClOS1qD2ItSX0Gc%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="49ngqld" data-popupid="49ngqld">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/28ae1ccaabc2453dadf850984ef9cf4e~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=Zb5zPJFScSnzCSbO9sFu4p0sTBk%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="dbvn8l2" data-popupid="dbvn8l2">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/douyin-user-image-file/d3bd91cc53ca5e3cbb5bd941d08fc334~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=o9UUS9BIdD6Od8OCOIC0NwU4ot8%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="qs5k8vt" data-popupid="qs5k8vt">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/douyin-user-file/5ed8ceac7f09c98a140446dfe5999ab0~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=J3ocvrdxZSJ%2F%2FJDmOGGO3q9pS1U%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="i2sw42m" data-popupid="i2sw42m">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/ok0qwAPNEDAsshIlDeftACgSZi5AV2E4xAzLyV~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=iy%2Fp1wiZBXQBHYZCyGokrrpisVU%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="ik9i481" data-popupid="ik9i481">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oYAAjvmuAFxXE6cyFYACaIQDjgNDUAiCMofofq~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=qMwez%2BuGqb4%2BD%2BgoeBE%2Fm3EUnIU%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="vyn3r4x" data-popupid="vyn3r4x">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-0813/ogKpHDZkIACsBmAA9AnEj2yAxEB9gAFemmCSof~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=MUi5Tq%2BdQn8AYbSJcDYOHfNSDZk%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="vf6xz1m" data-popupid="vf6xz1m">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-0813/oYAQfWIgCcAFOEIFD19DlZfLAqDzACAQ9ASmpJ~tplv-0wx4r9yasq-webp-resize:1024:1024.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=JY4i1EtxeECpfwz5jzlKwNiMliQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="u7qyaf7" data-popupid="u7qyaf7">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-o-0812/oYBAtqBXiAySKlU3AYISABhZ58qEIBAfQzkWYi~tplv-0wx4r9yasq-webp-resize:511:518.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=1Fi5KxejLaQhpRbCvHlvvh5uK24%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="aokdu99" data-popupid="aokdu99">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/5859f63c0bba491481933f67148a114c~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=gBFdAZ5awMLTKVvX562PWIHhjuk%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="bmm7zbr" data-popupid="bmm7zbr">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-image-file/418ebabd6f656e9a07f18e2e7b1cb886~tplv-0wx4r9yasq-webp-resize:1440:1090.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=kfMqxmbvkUdlzeLwJx9GrzpFnw0%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="3tyawtc" data-popupid="3tyawtc">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/douyin-user-image-file/5c70070a1c6feb10dba22921ba70ed85~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=CZ4YWhiXic6bhmxQjBvZTik%2BuMg%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="z0vlq16" data-popupid="z0vlq16">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/823ce1111bfb44808e3a51b9ee72ebac~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=jVSJI1sUgYMalsD4Ai25bC8tiws%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="miqjmcg" data-popupid="miqjmcg">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/fb7a06775c734c7397cc43b99de2a232~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=BeYkZt%2BVVqFR7fB2l8IfShPNRJA%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="n5thr75" data-popupid="n5thr75">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/2c4651dcfff04cd19e5e8fdacf5dfe69~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=%2FuqESXrAMwyj%2B4X8tyMcPG5WMv4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="r8wkrho" data-popupid="r8wkrho">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/4b667ff3076040ef945aed26cbbb4cde~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=KkpYItJJwiwUkjcQHTX%2FFdNL3GE%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="yccg512" data-popupid="yccg512">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/b25ad2162ac546e4bdb3dafe9de2b77d~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=lq7DoiYaTiXqzuiN8PDuErUdNRY%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="tl45g90" data-popupid="tl45g90">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/douyin-user-image-file/81341455169e406a4f3d080a20b7964d~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=rkFy3zJLBPV5YraZGtvA7SlnSZY%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="0c1haxz" data-popupid="0c1haxz">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/douyin-user-image-file/53fccb1ce8e383bd55d0f77f7ecf1482~tplv-0wx4r9yasq-webp-resize:1080:1471.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=0eKCFmyt9iLkUcuBpaWohrgr43s%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="zgq7be5" data-popupid="zgq7be5">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/douyin-user-image-file/9f56a141eb5b73b44c5e1a71ef573afa~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=ir4pX%2BEt1E8P0Azj87Fg6uE45uY%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="z9qy7fd" data-popupid="z9qy7fd">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-image-file/52ee1c56f7d886eb0681a624b81661dc~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=Puer4gPEp%2B03%2B6IMr8v2Tw%2Fm9b4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="d50g0et" data-popupid="d50g0et">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/douyin-user-image-file/b8df516cdeb4914a8b190c737d9bcd8c~tplv-0wx4r9yasq-webp-resize:1080:935.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=%2BDozX45rjZjard%2FDriujnozz%2Bac%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="zhkn5e1" data-popupid="zhkn5e1">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-image-file/8b356bb90fcdb16c7bfee3f2f8151e4b~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=nTM51BLfTdtmsIgIGbPoNe4m6yg%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="4z401xa" data-popupid="4z401xa">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/0ae8e2195f994d1eab4580d3c984d5a9~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=sH06winXz2%2Fipsq%2FVv%2FWrgQZOsA%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="yeav7vg" data-popupid="yeav7vg">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-o-0812/169b968d924545558261505e30ffcf4a~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=a0vWM%2F9nTCOFD29bgjlX25InayI%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="semceqa" data-popupid="semceqa">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/2e1a800047cad14fa5950~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=shWVeUa%2FyoUYssSla1QXWNlSSmo%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="rs28kp2" data-popupid="rs28kp2">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-image-file/c62c60f1222dc451e53e5878a1f7e843~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=nVvNlPoorLz61UEuEXpUh1n0wIQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="evwhc06" data-popupid="evwhc06">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/1356c3a92de440739b28bc6d9bf65d9d~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=kNaTr15rH5PqyTyWvkPJFFO8SnY%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="1ye9gb8" data-popupid="1ye9gb8">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/douyin-user-image-file/a07d7b55e3fcb495d69c3579f6f829dc~tplv-0wx4r9yasq-awebp-resize:0:0.awebp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=PjCn3Mj2Mg1%2BmiKF5vIzAhPbCpg%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="sj8znpg" data-popupid="sj8znpg">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/206934b02c164e48911c557a0aa3f2d9~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=7XtgTVM5TxMAq%2BQ4ecw6lyTdcb4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="9hrkztu" data-popupid="9hrkztu">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-file/531a4f1d58758c94156ce37c80f33788~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=k4gJ%2BFhtypJEpfjeH2tzyeGktWQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="x48ga30" data-popupid="x48ga30">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/2bc9860cfbd046d8b4beb56bf7177264~tplv-0wx4r9yasq-webp-resize:1000:1000.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=gSSmvda%2FSWtYhkLldem4vR4A50g%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="bpcpx0c" data-popupid="bpcpx0c">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/douyin-user-image-file/ef0432f975af8ca547da11adec5ebe52~tplv-0wx4r9yasq-webp-resize:1080:1419.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=4iBJo91dGL99sGuXGKFgakjV7KQ%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="v5yzy4s" data-popupid="v5yzy4s">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/douyin-user-file/34551c6a9db3d47a472eb327106fc7bb~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=NomAjaY83swCHBkUQsVGLngJiXE%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="1rwk3zs" data-popupid="1rwk3zs">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/douyin-user-image-file/e6285c5c35a24d23ffcc77bc917673ea~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=o5uuP1u2N0qI0DndAIJezMoeIPc%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="du6birx" data-popupid="du6birx">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-image-file/511501a06431d8d792a930a09d327d5d~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=TLJ%2BF9xayz0s%2FSF%2BsONRhYXhoa4%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="hu1kzip" data-popupid="hu1kzip">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-image-file/7fc3653a3aa37b92cc4559e6d9718bc5~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=oRj11E0zvi2qScSo5kMGG%2Bccxrs%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="lbqovd0" data-popupid="lbqovd0">
      <img class="kcsILzHu a05QVkMb" src="https://p3-im-emoticon-sign.byteimg.com/douyin-user-file/9c6bd3e750d0eaf3bdf6796dd1382f30~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=TivaLMpKucVRcMWXmk9CkQUivTY%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="3sp2wqh" data-popupid="3sp2wqh">
      <img class="kcsILzHu a05QVkMb" src="https://p9-im-emoticon-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/bbbbe76585c44a59baea371e5688b18c~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=iZpvBG1VQLDOJEWbactdyw48E2U%3D"></div>
  </div>
  <div class="QIM57_rn">
    <div class="jdLnfESQ KSCSb9Lp" tabindex="0" aria-describedby="ylexeou" data-popupid="ylexeou">
      <img class="kcsILzHu a05QVkMb" src="https://p26-im-emoticon-sign.byteimg.com/douyin-user-image-file/0a0a9f821b5f2c6c804a6e358b4f68cd~tplv-0wx4r9yasq-webp-resize:0:0.webp?biz_tag=aweme_im&amp;lk3s=91c5b7cb&amp;s=im_123&amp;sc=emotion&amp;x-expires=1781187037&amp;x-signature=CWt4P68vmpSomD0Xl6781RHQVhw%3D"></div>
  </div>
</div>
"""


def get_html_content(file_path=None, default_content=""):
    """
    获取HTML内容。
    如果提供了file_path，则尝试从文件读取。
    否则，使用default_content。
    """
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"警告: HTML文件 '{file_path}' 未找到，将使用默认内容 (如果提供)。")
        except Exception as e:
            print(f"警告: 读取HTML文件 '{file_path}' 时发生错误: {e}，将使用默认内容。")
    if default_content and default_content.strip():
        return default_content
    print("错误: 未提供有效的HTML内容或文件路径。")
    return None


def extract_image_urls_from_html(html_content_str):
    """解析HTML并提取图片URL及其推测的原始扩展名。"""
    if not html_content_str:
        return []
    soup = BeautifulSoup(html_content_str, 'html.parser')
    # 更新的选择器以匹配新的HTML结构
    img_tags = soup.select('.tfZqWdXG .jdLnfESQ img.kcsILzHu.LOP5yfbO')
    if not img_tags:
        # 如果新选择器失败，则回退到原始选择器
        img_tags = soup.select('.JQ9dA4iS .kcsILzHu.a05QVkMb')  # 这是一个旧的选择器示例，根据实际情况调整
        if not img_tags:
            print("警告: 主要和备用CSS选择器均未找到图片，尝试查找所有<img>标签。")
            img_tags = soup.find_all('img')

    urls_data = []
    for img in img_tags:
        if 'src' in img.attrs:
            url = img['src']
            if url and not url.startswith(('data:', 'javascript:')) and url.strip():
                original_ext = get_image_extension_from_url(url)
                urls_data.append(
                    {'url': url, 'ext': original_ext, 'original_filename_hint': os.path.basename(urlparse(url).path)})
            else:
                print(f"  跳过无效或不支持的src: {url[:50]}...")
    return urls_data


def get_image_extension_from_url(url):
    """从URL推断图片扩展名。"""
    try:
        path = urlparse(url).path
        _, ext = os.path.splitext(path)
        # 首先检查路径中的特定模式
        if 'tplv-0wx4r9yasq-awebp' in path or '.awebp' in path.lower(): return 'webp'
        if 'tplv-0wx4r9yasq-png' in path or '.png' in path.lower(): return 'png'
        if 'tplv-0wx4r9yasq-gif' in path or '.gif' in path.lower(): return 'gif'
        if 'tplv-0wx4r9yasq-jpeg' in path or '.jpeg' in path.lower(): return 'jpeg'  # jpeg通常指jpg
        if 'tplv-0wx4r9yasq-jpg' in path or '.jpg' in path.lower(): return 'jpeg'  # 统一为jpeg

        if ext and ext.lower() in ['.gif', '.jpg', '.jpeg', '.png', '.webp', '.awebp']:
            clean_ext = ext.lower().lstrip('.')
            if clean_ext == 'awebp': return 'webp'
            if clean_ext == 'jpg': return 'jpeg'  # 统一jpg为jpeg
            return clean_ext
    except Exception:
        pass  # 发生错误则继续尝试下面的回退检查
    # 对完整URL字符串的回退检查
    if 'tplv-0wx4r9yasq-awebp' in url or '.awebp' in url.lower(): return 'webp'
    if '.webp' in url.lower(): return 'webp'
    if '.gif' in url.lower(): return 'gif'
    if '.png' in url.lower(): return 'png'
    if '.jpg' in url.lower() or '.jpeg' in url.lower(): return 'jpeg'  # 统一jpg为jpeg
    print(f"  无法从URL确定扩展名: {url[:70]}... 默认设为 'bin' (二进制)")
    return 'bin'


def download_image_task(session, url_data, index, total_to_process):
    """
    下载单个图片的任务。
    返回其内容和元数据。
    'index' 是当前处理列表中的0基索引。
    'total_to_process' 是该列表中的项目总数。
    """
    url = url_data['url']
    original_ext = url_data['ext']
    # 为了用户显示，如果可用，使用原始列表中的索引
    display_index = url_data.get('original_list_index', index) + 1

    # 使用 \r 实现动态进度行，将被下一个状态或最终消息覆盖。
    print(f"\r[{display_index}/{total_to_process}] 下载中: {url[:60]}...", end="")

    try:
        response = session.get(url, stream=True, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # 如果状态码是4xx或5xx，则引发HTTPError
        # 打印此下载的完成消息，确保它覆盖 \r 行。
        # 在末尾添加空格以清除之前可能存在的较长行。
        print(
            f"\r[{display_index}/{total_to_process}] 下载完成: {url[:60]}... (大小: {len(response.content) / 1024:.2f} KB)      ")
        return {'index': index, 'original_list_index': url_data.get('original_list_index', index),
                'url': url, 'bytes': response.content, 'ext': original_ext, 'status': 'success'}
    except requests.exceptions.Timeout:
        print(f"\r[{display_index}/{total_to_process}] 下载超时: {url[:60]}...                                  ")
        return {'index': index, 'original_list_index': url_data.get('original_list_index', index),
                'url': url, 'error': 'Timeout', 'status': 'failed'}
    except requests.exceptions.HTTPError as e:
        print(
            f"\r[{display_index}/{total_to_process}] 下载失败 (HTTP {e.response.status_code}): {url[:60]}...         ")
        return {'index': index, 'original_list_index': url_data.get('original_list_index', index),
                'url': url, 'error': f'HTTP {e.response.status_code}', 'status': 'failed'}
    except requests.exceptions.RequestException as e:  # 其他网络相关错误
        print(f"\r[{display_index}/{total_to_process}] 下载网络错误: {url[:60]}... ({e})                      ")
        return {'index': index, 'original_list_index': url_data.get('original_list_index', index),
                'url': url, 'error': str(e), 'status': 'failed'}
    except Exception as e:  # 其他未知错误
        print(f"\r[{display_index}/{total_to_process}] 未知下载错误: {url[:60]}... ({e})                   ")
        return {'index': index, 'original_list_index': url_data.get('original_list_index', index),
                'url': url, 'error': f'Unknown: {str(e)}', 'status': 'failed'}


def convert_image_to_gif_bytes(image_bytes, original_ext, item_id_for_log=""):
    """
    将图片字节转换为GIF字节。
    item_id_for_log 是日志消息的前缀，如 "[1/10]"。
    返回 (gif_bytes, 'gif') 或 (None, None)。
    """
    if original_ext == 'gif':  # 如果原始就是GIF，理论上不应由此函数处理（应在包装器中处理）
        return image_bytes, 'gif'

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except UnidentifiedImageError:
        print(f"{item_id_for_log} Pillow无法识别图片格式: {original_ext}")
        return None, None
    except Exception as e:
        print(f"{item_id_for_log} Pillow打开图片时出错 ({original_ext}): {e}")
        return None, None

    frames = []
    durations = []
    loop = GIF_LOOP_COUNT  # 使用全局配置的循环次数

    try:
        if hasattr(img, 'n_frames') and img.n_frames > 1:
            # 动画图片 (例如，动画WebP)
            frame_duration_info = img.info.get('duration', GIF_DEFAULT_FRAME_DURATION)  # 可能是整数或列表

            for i in range(img.n_frames):
                img.seek(i)  # 定位到当前帧
                current_frame_duration = GIF_DEFAULT_FRAME_DURATION  # 当前帧的默认持续时间

                if isinstance(frame_duration_info, list):  # 如果duration是列表
                    if i < len(frame_duration_info):
                        current_frame_duration = frame_duration_info[i]
                elif isinstance(frame_duration_info, (int, float)):  # 如果duration是单个数字，则应用于所有帧
                    current_frame_duration = int(frame_duration_info)

                # 验证并确保持续时间为正，否则使用默认值
                if not isinstance(current_frame_duration, (int, float)) or current_frame_duration <= 0:
                    current_frame_duration = GIF_DEFAULT_FRAME_DURATION
                else:
                    current_frame_duration = int(current_frame_duration)

                durations.append(max(GIF_MIN_FRAME_DURATION, current_frame_duration))  # 确保不低于最小帧持续时间

                frame_converted = img.convert("RGBA")  # 确保为RGBA以进行一致处理和透明度支持
                if GIF_QUANTIZE_COLORS > 0:
                    # 应用量化以获得更好的GIF兼容性并可能减小文件大小
                    frame_quantized = frame_converted.quantize(
                        colors=GIF_QUANTIZE_COLORS,
                        method=GIF_QUANTIZE_METHOD,
                        dither=GIF_DITHER_METHOD
                    )
                    frames.append(frame_quantized.copy())  # 添加量化后的帧
                else:  # 不进行量化
                    frames.append(frame_converted.copy())
        else:
            # 静态图片
            frame_converted = img.convert("RGBA")
            if GIF_QUANTIZE_COLORS > 0:
                frames.append(frame_converted.quantize(colors=GIF_QUANTIZE_COLORS, method=GIF_QUANTIZE_METHOD,
                                                       dither=GIF_DITHER_METHOD).copy())
            else:
                frames.append(frame_converted.copy())
            durations.append(GIF_DEFAULT_FRAME_DURATION)  # 单个静态帧的持续时间
            loop = 0  # 静态GIF不应循环帧 (Pillow对于单帧可能会忽略loop=0)

    except EOFError:  # 读取多帧图片时遇到文件结束错误
        print(f"{item_id_for_log} 读取多帧图片时遇到EOFError ({original_ext})。尝试保存已提取帧或首帧。")
        if not frames:  # 如果在EOF之前没有成功处理任何帧
            try:
                img.seek(0)  # 尝试至少挽救第一帧
                frame_converted = img.convert("RGBA")
                if GIF_QUANTIZE_COLORS > 0:
                    frames.append(frame_converted.quantize(colors=GIF_QUANTIZE_COLORS, method=GIF_QUANTIZE_METHOD,
                                                           dither=GIF_DITHER_METHOD).copy())
                else:
                    frames.append(frame_converted.copy())
                durations.append(GIF_DEFAULT_FRAME_DURATION)
                loop = 0
            except Exception as e_seek:
                print(f"{item_id_for_log} 尝试读取第一帧失败: {e_seek}")
                return None, None
    except Exception as e:
        print(f"{item_id_for_log} 提取帧时发生错误 ({original_ext}): {e}")
        return None, None

    if not frames:
        print(f"{item_id_for_log} 未能从 ({original_ext}) 提取任何帧用于GIF转换。")
        return None, None

    gif_bytes_io = io.BytesIO()  # 用于在内存中保存GIF数据
    try:
        frames[0].save(
            gif_bytes_io,
            format='GIF',
            save_all=True,  # 保存所有帧 (用于动画GIF)
            append_images=frames[1:],  # 附加剩余的帧
            duration=durations,  # 每帧的持续时间列表
            loop=loop,  # 循环次数
            optimize=GIF_OPTIMIZE,  # 是否优化
            # transparency= 处理透明度比较复杂，这里Pillow会自动处理一些情况，但完美控制需要更细致的逻辑
            disposal=2  # 处置方法2: Restore to background。对于带透明度的动画通常效果较好
        )
        return gif_bytes_io.getvalue(), 'gif'
    except Exception as e:
        print(f"{item_id_for_log} 保存为GIF时发生错误: {e}")
        return None, None


def conversion_task_wrapper(download_data, total_items_being_processed):
    """
    图片转换任务的包装器。接收成功下载的数据。
    返回包含处理结果的字典。
    """
    original_idx_in_list = download_data['index']  # 当前处理列表中的0基索引
    # 从完整提取列表中获取实际的0基索引
    original_list_idx = download_data.get('original_list_index', original_idx_in_list)
    url = download_data['url']
    original_ext = download_data['ext']
    image_bytes = download_data['bytes']

    # 日志消息的前缀，使用原始列表索引
    log_prefix = f"[{original_list_idx + 1}/{total_items_being_processed}]"

    if original_ext == 'gif':
        # print(f"{log_prefix} 完成转换: {url[:50]}... (原始为GIF)") # 可选：记录完成日志
        return {
            'original_data': download_data,
            'final_bytes': image_bytes,
            'final_ext': 'gif',
            'message': "原始为GIF",
            'status': 'processed_as_is'  # 按原样处理
        }

    converted_bytes, new_ext = convert_image_to_gif_bytes(image_bytes, original_ext, item_id_for_log=log_prefix)

    if converted_bytes and new_ext == 'gif':
        # print(f"{log_prefix} 完成转换: {url[:50]}... (已转为GIF)") # 可选：记录完成日志
        return {
            'original_data': download_data,
            'final_bytes': converted_bytes,
            'final_ext': 'gif',
            'message': "已转换为GIF",
            'status': 'processed_converted'  # 已转换处理
        }
    else:
        # print(f"{log_prefix} 完成转换: {url[:50]}... (GIF转换失败, 保留原始 {original_ext})") # 可选：记录完成日志
        return {
            'original_data': download_data,
            'final_bytes': image_bytes,  # 回退到原始字节
            'final_ext': original_ext,  # 回退到原始扩展名
            'message': f"GIF转换失败，保留原始 {original_ext}",
            'status': 'processed_conversion_failed'  # 转换失败处理
        }


def main():
    """主函数，协调下载、转换和压缩过程。"""
    actual_html_content = get_html_content(HTML_CONTENT_FILE, html_content)
    if not actual_html_content:
        return

    all_urls_data = extract_image_urls_from_html(actual_html_content)
    if not all_urls_data:
        print("HTML解析后未找到有效图片链接。")
        return

    total_found_images = len(all_urls_data)
    print(f"总共找到 {total_found_images} 个图片链接。")

    # 应用 MAX_EMOTICONS_TO_DOWNLOAD 限制
    urls_to_process = []
    # 正确分配 original_list_index，基于*完整*的找到的URL列表
    # 这确保即使我们只下载一个子集，它们的文件名（如emoticon_001）
    # 也对应于它们在最初发现的完整列表中的顺序。
    temp_urls_to_process = []
    if MAX_EMOTICONS_TO_DOWNLOAD > 0 and MAX_EMOTICONS_TO_DOWNLOAD < total_found_images:
        print(f"限制处理数量: 将只下载和处理前 {MAX_EMOTICONS_TO_DOWNLOAD} 个表情。")
        for i in range(MAX_EMOTICONS_TO_DOWNLOAD):
            data_item = all_urls_data[i].copy()  # 复制以避免修改原始列表项
            data_item['original_list_index'] = i  # 在完整列表中的索引
            temp_urls_to_process.append(data_item)
        urls_to_process = temp_urls_to_process
    else:  # 下载所有找到的，或者配置数量大于等于找到的数量
        if MAX_EMOTICONS_TO_DOWNLOAD > 0:
            print(
                f"配置的下载数量 {MAX_EMOTICONS_TO_DOWNLOAD} 大于或等于找到的数量 {total_found_images}。将处理所有找到的表情。")
        for i in range(len(all_urls_data)):
            data_item = all_urls_data[i].copy()
            data_item['original_list_index'] = i
            temp_urls_to_process.append(data_item)
        urls_to_process = temp_urls_to_process

    num_to_process = len(urls_to_process)  # 实际要处理的项目数量
    if num_to_process == 0:
        print("没有要处理的图片 (可能因为限制数量为0或未找到图片)。")
        return

    # --- 阶段 1: 下载 ---
    print(f"\n--- 开始下载 {num_to_process} 个表情 (最大 {MAX_DOWNLOAD_WORKERS} 个线程) ---")
    downloaded_images_data = []  # 存储下载结果
    with requests.Session() as session, concurrent.futures.ThreadPoolExecutor(
            max_workers=MAX_DOWNLOAD_WORKERS) as executor:
        session.headers.update({  # 设置用户代理，模拟浏览器请求
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # 'i' 是 'urls_to_process' 列表的索引 (0 到 num_to_process-1)
        # 'num_to_process' 是我们实际处理的总数
        future_to_url_data = {
            executor.submit(download_image_task, session, url_data_item, i, num_to_process): url_data_item
            for i, url_data_item in enumerate(urls_to_process)
        }
        for future in concurrent.futures.as_completed(future_to_url_data):
            downloaded_images_data.append(future.result())
    print("\n--- 所有下载任务完成 ---")

    # 按其在处理列表中的索引对下载结果进行排序
    downloaded_images_data.sort(key=lambda x: x['index'])

    successful_downloads = [d for d in downloaded_images_data if d['status'] == 'success']
    failed_download_count = num_to_process - len(successful_downloads)
    print(
        f"下载结果: {len(successful_downloads)} 成功, {failed_download_count} 失败 (在计划处理的 {num_to_process} 个中).")

    if not successful_downloads:
        print("没有成功下载的图片，程序退出。")
        return

    # --- 阶段 2: 转换 ---
    results_after_processing = []  # 将存储所有结果（下载失败、转换结果）

    # 直接将下载失败的项目添加到最终列表中
    for item in downloaded_images_data:
        if item['status'] == 'failed':
            results_after_processing.append({
                'original_data': item, 'final_bytes': None, 'final_ext': None,
                'message': f"下载失败: {item.get('error', '未知错误')}",
                'status': 'download_failed'
            })

    print(f"\n--- 开始处理和转换 {len(successful_downloads)} 张图片 (最大 {MAX_CONVERSION_WORKERS} 个线程) ---")
    if successful_downloads:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONVERSION_WORKERS) as converter_executor:
            future_to_conversion_info = {
                # 将 'num_to_process' 作为总数传递给日志显示
                converter_executor.submit(conversion_task_wrapper, dl_data, num_to_process): dl_data
                for dl_data in successful_downloads
            }

            converted_count = 0
            for future in concurrent.futures.as_completed(future_to_conversion_info):
                try:
                    result = future.result()
                    results_after_processing.append(result)
                    # 使用 'original_list_index' 进行显示，以匹配项目的真实序列号
                    display_idx = result['original_data'].get('original_list_index',
                                                              result['original_data']['index']) + 1
                    print(
                        f"\r[{display_idx}/{num_to_process}] 处理完成: {result['original_data']['url'][:45]}... {result['message']}                                ")

                except Exception as e:  # 处理 conversion_task_wrapper 本身的意外错误
                    dl_data = future_to_conversion_info[future]
                    display_idx = dl_data.get('original_list_index', dl_data['index']) + 1
                    print(
                        f"\r[{display_idx}/{num_to_process}] 转换任务内部错误 for {dl_data['url'][:45]}: {e}        ")
                    results_after_processing.append({
                        'original_data': dl_data, 'final_bytes': dl_data['bytes'], 'final_ext': dl_data['ext'],
                        'message': f"转换任务严重错误: {e}",
                        'status': 'processed_conversion_error_critical'  # 转换过程中发生严重错误
                    })
                converted_count += 1
                # 总体进度 (可选, 因为会打印单独的行)
                # print(f"\r转换进度: {converted_count}/{len(successful_downloads)} 完成.", end="")

    print("\n--- 所有转换任务完成 ---")

    # 按原始索引对所有结果进行排序，以确保一致的压缩顺序
    results_after_processing.sort(
        key=lambda x: x['original_data'].get('original_list_index', x['original_data']['index']))

    # --- 阶段 3: 压缩 ---
    successfully_processed_for_zip_count = len([
        d for d in results_after_processing
        if d['status'] in ['processed_as_is', 'processed_converted', 'processed_conversion_failed',
                           'processed_conversion_error_critical']
        # 所有至少已下载的项目（包括转换失败但仍保留原始文件的）
    ])

    print(f"\n--- 开始压缩 {successfully_processed_for_zip_count} 个项目到 {ZIP_FILENAME} ---")
    zip_count = 0
    with zipfile.ZipFile(ZIP_FILENAME, 'w', zipfile.ZIP_DEFLATED) as zipf:  # 使用DEFLATED压缩方法
        for item_data in results_after_processing:
            original_item_info = item_data['original_data']
            # 使用 'original_list_index' 进行文件名和日志前缀，以确保与发现的表情完整列表相关的编号一致。
            file_num_idx = original_item_info.get('original_list_index', original_item_info['index'])
            url = original_item_info['url']
            log_prefix = f"[{file_num_idx + 1}/{num_to_process}]"  # 显示相对于正在处理的项目的进度

            if item_data['status'] == 'download_failed':
                print(f"{log_prefix} 跳过压缩 (下载失败): {url[:60]} ({item_data['message']})")
                continue

            # 如果转换任务出现严重错误，它仍可能尝试压缩原始字节
            if item_data['status'] == 'processed_conversion_error_critical':
                print(f"{log_prefix} 注意 (转换任务严重错误，尝试压缩原始): {url[:60]} ({item_data['message']})")

            base_filename = f"emoticon_{file_num_idx + 1:03d}"  # 文件名基于原始完整列表顺序，例如 emoticon_001
            final_bytes_to_zip = item_data['final_bytes']
            final_extension_for_zip = item_data['final_ext']

            if final_bytes_to_zip is None or final_extension_for_zip is None:  # 如果没有有效数据则跳过
                print(f"{log_prefix} 跳过压缩 (无有效数据): {url[:60]}")
                continue

            filename_in_zip = f"{base_filename}.{final_extension_for_zip}"
            try:
                zipf.writestr(filename_in_zip, final_bytes_to_zip)  # 将字节数据写入ZIP文件
                zip_count += 1
                # 消息已由转换阶段打印或由 'download_failed' 处理
                # 对于压缩，只需确认或错误信息。
                print(f"{log_prefix} 已压缩 {url[:50]}... 为 {filename_in_zip} ({item_data['message']})")
            except Exception as e:
                print(f"{log_prefix} 添加到ZIP失败: {filename_in_zip} ({url[:50]}) (错误: {e})")

    print(f"\n--- 压缩完成 ---")
    print(f"{zip_count} 个文件已添加到 {ZIP_FILENAME}。")
    print(f"\n全部流程完成！")


# --- 主程序入口 ---
if __name__ == "__main__":

    main()