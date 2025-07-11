"""
UrlをEmbedlyカードに変換するMarkdown拡張機能
この拡張機能は、Markdown内で特定の形式のURLをEmbedlyカードに変換します。
"""

from markdown import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.postprocessors import Postprocessor
from markdown.util import etree
from urllib.parse import urlparse

__all__ = ['EmbedlyExtension']

class EmbedlyExtension(Extension):
    """EmbedlyカードをMarkdownで生成するための拡張機能"""
    
    # デフォルト設定を定数として定義
    DEFAULT_CONFIG = {
        'default_title': ['Embedded content', 'デフォルトのタイトル'],
        'default_type': ['article', 'デフォルトのカードタイプ（article/video/imageなど）'],
        'allowed_domains': [[], '許可するドメインのリスト（空の場合は全て許可）'],
        'card_controls': ['0', 'シェアボタンを表示するか（0:非表示, 1:表示）'],
        'card_align': ['left', '画像の配置（left/center/right）'],
        'card_width': ['100%', 'カードの幅（CSSのwidthプロパティ）'],
        'card_theme': ['default', 'カードのテーマ（default/dark/lightなど）'],
        'card_key': ['', 'Embedly APIキー'],
        'script_position': ['after', 'スクリプトの位置（after/before/none）'],
        'script_async': [True, 'スクリプトを非同期で読み込むか'],
    }

    EMBED_PATTERN = r'\[!embed(?::(?P<type>\w+))?\s+(?P<url>[^\s\]]+)(?:\s+(?P<title>[^\]]+))?\]'
    
    def __init__(self, **kwargs):
        self.config = self.DEFAULT_CONFIG.copy()
        super().__init__(**kwargs)
    
    def extendMarkdown(self, md):
        """Markdownパーサーに拡張機能を追加"""
        embed_processor = EmbedlyInlineProcessor(
            self.EMBED_PATTERN,
            md,
            self
        )
        md.inlinePatterns.register(embed_processor, 'embedly', 175)
        
        # スクリプトを追加するためのPostProcessor
        if self.getConfig('script_position') != 'none':
            script_processor = EmbedlyScriptProcessor(md, self)
            md.postprocessors.register(script_processor, 'embedly_script', 10)


class EmbedlyInlineProcessor(InlineProcessor):
    """Embedlyカードの変換を行うInlineProcessor"""
    
    def __init__(self, pattern: str, md, extension: EmbedlyExtension):
        super().__init__(pattern, md)
        self.extension = extension
    
    def handleMatch(self, m, data):
        """マッチしたパターンを処理してEmbedlyカードまたはテキストを生成"""
        url = m.group('url')
        
        if not self._is_valid_url(url):
            # 無効なURLの場合は元のテキストを返す
            return self._create_text_element(m.group(0)), m.start(0), m.end(0)
        
        # カードのタイプとタイトルを取得
        card_type = m.group('type') or self.extension.getConfig('default_type')
        title = m.group('title') or self.extension.getConfig('default_title')
        
        embed_element = self._create_embed_element(url, card_type, title)
        return embed_element, m.start(0), m.end(0)
    
    def _is_valid_url(self, url: str) -> bool:
        """URLの妥当性をチェック"""
        try:
            parsed = urlparse(url)
            if not self._has_valid_scheme_and_netloc(parsed):
                return False
            
            return self._is_domain_allowed(parsed.netloc)
        except Exception:
            return False
    
    def _has_valid_scheme_and_netloc(self, parsed_url) -> bool:
        """URLがスキームとネットワークロケーションを持つか"""
        return bool(parsed_url.scheme and parsed_url.netloc)
    
    def _is_domain_allowed(self, netloc: str) -> bool:
        """ドメインが許可されているか"""
        allowed_domains = self.extension.getConfig('allowed_domains')
        if not allowed_domains:
            return True
        
        domain = netloc.lower()
        return any(domain.endswith(str(allowed).lower()) for allowed in allowed_domains)
    
    def _create_embed_element(self, url: str, card_type: str, title: str) -> etree.Element:
        """Embedlyカード要素を作成"""
        a_element = etree.Element('a')
        
        # 属性を設定
        attributes = {
            'class': 'embedly-card',
            'href': url,
            'data-card-type': card_type,
            'data-card-controls': str(self.extension.getConfig('card_controls')),
            'data-card-align': str(self.extension.getConfig('card_align')),
            'data-card-width': str(self.extension.getConfig('card_width')),
            'data-card-theme': str(self.extension.getConfig('card_theme')),
        }

        if self.extension.getConfig('card_key'):
            attributes['data-card-key'] = self.extension.getConfig('card_key')
        
        for key, value in attributes.items():
            a_element.set(key, value)
        
        a_element.text = title
        return a_element
    
    def _create_text_element(self, text: str) -> etree.Element:
        """テキスト要素を作成"""
        span_element = etree.Element('span')
        span_element.text = text
        return span_element


class EmbedlyScriptProcessor(Postprocessor):
    """Embedlyスクリプトを追加するPostProcessor"""
    
    SCRIPT_URL = "https://cdn.embedly.com/widgets/platform.js"
    EMBEDLY_CARD_CLASS = 'embedly-card'
    
    def __init__(self, md, extension: EmbedlyExtension):
        super().__init__(md)
        self.extension = extension
    
    def run(self, text: str) -> str:
        """HTMLにEmbedlyスクリプトを追加"""
        # embedly-cardクラスが存在する場合のみスクリプトを追加
        if self.EMBEDLY_CARD_CLASS not in text:
            return text
        
        script_html = self._create_script_html()
        return self._insert_script(text, script_html)
    
    def _create_script_html(self) -> str:
        async_attr = ' async' if self.extension.getConfig('script_async') else ''
        return f'<script{async_attr} src="{self.SCRIPT_URL}" charset="UTF-8"></script>'
    
    def _insert_script(self, html: str, script_html: str) -> str:
        script_position = self.extension.getConfig('script_position')
        
        if script_position == 'before':
            return script_html + html
        elif script_position == 'after':
            return html + script_html
        return html

def makeExtension(*args, **kwargs):
    return EmbedlyExtension(*args, **kwargs)
