https://peter.sh/experiments/chromium-command-line-switches/

chrome options args

```bash
$ pip install selenium
$ wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
$ sudo dpkg -i google-chrome-stable_current_amd64.deb
```

## check chrome version

https://chromedriver.storage.googleapis.com/

part of view
```
<Contents>
    <Key>75.0.3770.140/chromedriver_linux64.zip</Key>
    <Generation>1562954785447657</Generation>
    <MetaGeneration>1</MetaGeneration>
    <LastModified>2019-07-12T18:06:25.447Z</LastModified>
    <ETag>"352fa37b124b9ddfd458439bbb877ac5"</ETag>
    <Size>5139472</Size>
</Contents>
```

75.0.3770.140 找最靠近的version，但不能大於

https://chromedriver.storage.googleapis.com/83.0.4103.14/notes.txt

> $ wget https://chromedriver.storage.googleapis.com/{chrome_version}/chromedriver_linux64.zip  
$ unzip chromedriver_linux64.zip  
$ chmod +x chromedriver  
$ sudo mv chromedriver /usr/bin/