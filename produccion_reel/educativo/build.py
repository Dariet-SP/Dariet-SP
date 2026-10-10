import base64,re,sys
src=open('usage_src.html').read()
def emb(m):
    path='../build/node_modules/@fontsource/montserrat/files/'+m.group(1)
    b=base64.b64encode(open(path,'rb').read()).decode()
    return 'url(data:font/woff2;base64,'+b+')'
out=re.sub(r"url\(\.\./build/node_modules/@fontsource/montserrat/files/([^)]+)\)",emb,src)
open('usage_final.html','w').write(out)
print(len(out))
