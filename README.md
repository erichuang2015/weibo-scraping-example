# weibo-scraping-example
scraping China SNS Weibo contents using selenium and beautifulsoup4

<pre>
            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.
</pre>

### Usage
Python >= 3.6

```python
>>> pip install -r requirements.txt
>>> python weibo.py
```
Your weibo loginname and password will be asked for the first time. Please make sure you have a account that doesn't require verification code to login.

### About Selenium
Selenium requires a driver to interface with the chosen browser. Firefox, for example, requires geckodriver, which needs to be installed before the below examples can be run. Make sure it’s in your PATH, e. g., place it in /usr/bin or /usr/local/bin.

driver | link
------------ | -------------
Chrome:	| https://sites.google.com/a/chromium.org/chromedriver/downloads
Edge:	| https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
Firefox:	| https://github.com/mozilla/geckodriver/releases
Safari:	| https://webkit.org/blog/6900/webdriver-support-in-safari-10/
