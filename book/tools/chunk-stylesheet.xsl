<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version='1.0'>

  <xsl:import href="xsl/html/chunk.xsl"/>
  <xsl:import href="xsl/html/profile-chunk.xsl"/>

  <xsl:output method="html" encoding="UTF-8" indent="no"/>

  <!-- Force chunk files (and their <meta charset>) to UTF-8.  Without this,
       DocBook XSL falls back to chunker.output.encoding=ISO-8859-1, which
       leaks raw 0xA0/0xA9 bytes (nbsp, ©) into the page; under a server
       that serves the chunked dir as UTF-8 those bytes render as �. -->
  <xsl:param name="chunker.output.encoding">UTF-8</xsl:param>
  <xsl:param name="use.id.as.filename">1</xsl:param>

  <xsl:param name="html.stylesheet">styles.css</xsl:param>
  <xsl:param name="toc.section.depth">3</xsl:param>
  <xsl:param name="annotate.toc">0</xsl:param>
  <xsl:param name="profile.condition">none</xsl:param>

  <xsl:template match="sect1" mode="toc">
    <xsl:param name="toc-context" select="."/>
    <xsl:call-template name="subtoc">
      <xsl:with-param name="toc-context" select="$toc-context"/>
      <xsl:with-param name="nodes" 
        select="sect2|refentry|bridgehead[$bridgehead.in.toc != 0]"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="sect2" mode="toc">
    <xsl:param name="toc-context" select="."/>

    <xsl:call-template name="subtoc">
      <xsl:with-param name="toc-context" select="$toc-context"/>
      <xsl:with-param name="nodes" 
        select="sect3|refentry|bridgehead[$bridgehead.in.toc != 0]"/>
    </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>
