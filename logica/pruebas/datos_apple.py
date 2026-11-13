"""XMP con la misma forma que el que escribe Fotos de iOS (copiado de una foto real,
con otro texto)."""

XMP_SOLO_DESCRIPCION = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 6.0.0"> '
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"> '
    '<rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/" '
    'xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/" '
    'xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" '
    'xmp:CreateDate="2026-11-11T10:56:28" photoshop:DateCreated="2026-11-11T10:56:28+01:00" '
    'Iptc4xmpExt:ArtworkContentDescription="Un cielo al atardecer sobre el mar."/> '
    '</rdf:RDF> </x:xmpmeta>')

XMP_CON_PIE_DE_FOTO = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 6.0.0"> '
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"> '
    '<rdf:Description rdf:about="" xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'Iptc4xmpExt:ArtworkContentDescription="Un barco atracado en el puerto"> '
    '<dc:description> <rdf:Alt> <rdf:li xml:lang="x-default">Un barco atracado en el puerto</rdf:li> '
    '</rdf:Alt> </dc:description> </rdf:Description> </rdf:RDF> </x:xmpmeta>')
