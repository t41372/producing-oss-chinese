<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                version='1.0'>
  <xsl:import href="xsl/fo/docbook.xsl"/>
  <xsl:import href="xsl/fo/profile-docbook.xsl"/>

  <xsl:param name="alignment">left</xsl:param>
  <xsl:param name="fop1.extensions" select="1" />
  <xsl:param name="variablelist.as.blocks" select="1" />
  <xsl:param name="profile.condition">treeware</xsl:param>
  <xsl:param name="insert.xref.page.number">yes</xsl:param>

  <xsl:param name="page.margin.inner">15mm</xsl:param>
  <xsl:param name="page.margin.outer">10mm</xsl:param>
  <xsl:param name="body.start.indent">5mm</xsl:param>
  <xsl:param name="paper.type" select="'B5'"></xsl:param>

  <xsl:param name="body.font.family">WenQuanYi Zen Hei, Noto Sans CJK SC, sans-serif</xsl:param>
  <xsl:param name="title.font.family">WenQuanYi Zen Hei, Noto Sans CJK SC, sans-serif</xsl:param>
  <xsl:param name="monospace.font.family">WenQuanYi Zen Hei Mono, Noto Sans Mono CJK SC, monospace</xsl:param>

  <xsl:attribute-set name="component.title.properties">
    <xsl:attribute name="font-style">normal</xsl:attribute>
  </xsl:attribute-set>

  <xsl:attribute-set name="section.title.properties">
    <xsl:attribute name="font-style">normal</xsl:attribute>
  </xsl:attribute-set>

  <xsl:template name="inline.italicseq">
    <xsl:param name="content">
      <xsl:apply-templates/>
    </xsl:param>
    <xsl:choose>
      <xsl:when test="ancestor-or-self::*[@lang='zh']">
        <fo:inline font-weight="bold">
          <xsl:call-template name="anchor"/>
          <xsl:copy-of select="$content"/>
        </fo:inline>
      </xsl:when>
      <xsl:otherwise>
        <fo:inline font-style="italic">
          <xsl:call-template name="anchor"/>
          <xsl:copy-of select="$content"/>
        </fo:inline>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>
