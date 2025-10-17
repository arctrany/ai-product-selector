Skip to main content
Playwright logo
Playwright for Python
Docs
API
Python
Community

API reference
Playwright
Classes
APIRequest
APIRequestContext
APIResponse
Accessibility
Browser
BrowserContext
BrowserType
CDPSession
Clock
ConsoleMessage
Dialog
Download
ElementHandle
Error
FileChooser
Frame
FrameLocator
JSHandle
Keyboard
Locator
Mouse
Page
Request
Response
Route
Selectors
TimeoutError
Touchscreen
Tracing
Video
WebError
WebSocket
WebSocketRoute
Worker
Assertions
APIResponseAssertions
LocatorAssertions
PageAssertions
API referenceClassesBrowserType
BrowserType
BrowserType provides methods to launch a specific browser instance or connect to an existing one. The following is a typical example of using Playwright to drive automation:

Sync
Async
from playwright.sync_api import sync_playwright, Playwright

def run(playwright: Playwright):
chromium = playwright.chromium
browser = chromium.launch()
page = browser.new_page()
page.goto("https://example.com")
# other actions...
browser.close()

with sync_playwright() as playwright:
run(playwright)

Methods
connect
Added before v1.9
This method attaches Playwright to an existing browser instance created via BrowserType.launchServer in Node.js.

note
The major and minor version of the Playwright instance that connects needs to match the version of Playwright that launches the browser (1.2.3 → is compatible with 1.2.x).

Usage

browser_type.connect(ws_endpoint)
browser_type.connect(ws_endpoint, **kwargs)

Arguments

ws_endpoint str Added in: v1.10#

A Playwright browser websocket endpoint to connect to. You obtain this endpoint via BrowserServer.wsEndpoint.

expose_network str (optional) Added in: v1.37#

This option exposes network available on the connecting client to the browser being connected to. Consists of a list of rules separated by comma.

Available rules:

Hostname pattern, for example: example.com, *.org:99, x.*.y.com, *foo.org.
IP literal, for example: 127.0.0.1, 0.0.0.0:99, [::1], [0:0::1]:99.
<loopback> that matches local loopback interfaces: localhost, *.localhost, 127.0.0.1, [::1].
Some common examples:

"*" to expose all network.
"<loopback>" to expose localhost network.
"*.test.internal-domain,*.staging.internal-domain,<loopback>" to expose test/staging deployments and localhost.
headers Dict[str, str] (optional) Added in: v1.11#

Additional HTTP headers to be sent with web socket connect request. Optional.

slow_mo float (optional) Added in: v1.10#

Slows down Playwright operations by the specified amount of milliseconds. Useful so that you can see what is going on. Defaults to 0.

timeout float (optional) Added in: v1.10#

Maximum time in milliseconds to wait for the connection to be established. Defaults to 0 (no timeout).

Returns

Browser#
connect_over_cdp
Added in: v1.9
This method attaches Playwright to an existing browser instance using the Chrome DevTools Protocol.

The default browser context is accessible via browser.contexts.

note
Connecting over the Chrome DevTools Protocol is only supported for Chromium-based browsers.

note
This connection is significantly lower fidelity than the Playwright protocol connection via browser_type.connect(). If you are experiencing issues or attempting to use advanced functionality, you probably want to use browser_type.connect().

Usage

Sync
Async
browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
default_context = browser.contexts[0]
page = default_context.pages[0]

Arguments

endpoint_url str Added in: v1.11#

A CDP websocket endpoint or http url to connect to. For example http://localhost:9222/ or ws://127.0.0.1:9222/devtools/browser/387adf4c-243f-4051-a181-46798f4a46f4.

headers Dict[str, str] (optional) Added in: v1.11#

Additional HTTP headers to be sent with connect request. Optional.

slow_mo float (optional) Added in: v1.11#

Slows down Playwright operations by the specified amount of milliseconds. Useful so that you can see what is going on. Defaults to 0.

timeout float (optional) Added in: v1.11#

Maximum time in milliseconds to wait for the connection to be established. Defaults to 30000 (30 seconds). Pass 0 to disable timeout.

Returns

Browser#
launch
Added before v1.9
Returns the browser instance.

Usage

You can use ignore_default_args to filter out --mute-audio from default arguments:

Sync
Async
browser = playwright.chromium.launch( # or "firefox" or "webkit".
ignore_default_args=["--mute-audio"]
)

Chromium-only Playwright can also be used to control the Google Chrome or Microsoft Edge browsers, but it works best with the version of Chromium it is bundled with. There is no guarantee it will work with any other version. Use executable_path option with extreme caution.

If Google Chrome (rather than Chromium) is preferred, a Chrome Canary or Dev Channel build is suggested.

Stock browsers like Google Chrome and Microsoft Edge are suitable for tests that require proprietary media codecs for video playback. See this article for other differences between Chromium and Chrome. This article describes some differences for Linux users.

Arguments

args List[str] (optional)#

warning
Use custom browser args at your own risk, as some of them may break Playwright functionality.

Additional arguments to pass to the browser instance. The list of Chromium flags can be found here.

channel str (optional)#

Browser distribution channel.

Use "chromium" to opt in to new headless mode.

Use "chrome", "chrome-beta", "chrome-dev", "chrome-canary", "msedge", "msedge-beta", "msedge-dev", or "msedge-canary" to use branded Google Chrome and Microsoft Edge.

chromium_sandbox bool (optional)#

Enable Chromium sandboxing. Defaults to false.

devtools bool (optional)#

Deprecated
Use debugging tools instead.

Chromium-only Whether to auto-open a Developer Tools panel for each tab. If this option is true, the headless option will be set false.

downloads_path Union[str, pathlib.Path] (optional)#

If specified, accepted downloads are downloaded into this directory. Otherwise, temporary directory is created and is deleted when browser is closed. In either case, the downloads are deleted when the browser context they were created in is closed.

env Dict[str, str | float | bool] (optional)#

Specify environment variables that will be visible to the browser. Defaults to process.env.

executable_path Union[str, pathlib.Path] (optional)#

Path to a browser executable to run instead of the bundled one. If executable_path is a relative path, then it is resolved relative to the current working directory. Note that Playwright only works with the bundled Chromium, Firefox or WebKit, use at your own risk.

firefox_user_prefs Dict[str, str | float | bool] (optional)#

Firefox user preferences. Learn more about the Firefox user preferences at about:config.

You can also provide a path to a custom policies.json file via PLAYWRIGHT_FIREFOX_POLICIES_JSON environment variable.

handle_sighup bool (optional)#

Close the browser process on SIGHUP. Defaults to true.

handle_sigint bool (optional)#

Close the browser process on Ctrl-C. Defaults to true.

handle_sigterm bool (optional)#

Close the browser process on SIGTERM. Defaults to true.

headless bool (optional)#

Whether to run browser in headless mode. More details for Chromium and Firefox. Defaults to true unless the devtools option is true.

ignore_default_args bool | List[str] (optional)#

If true, Playwright does not pass its own configurations args and only uses the ones from args. If an array is given, then filters out the given default arguments. Dangerous option; use with care. Defaults to false.

proxy Dict (optional)#

server str

Proxy to be used for all requests. HTTP and SOCKS proxies are supported, for example http://myproxy.com:3128 or socks5://myproxy.com:3128. Short form myproxy.com:3128 is considered an HTTP proxy.

bypass str (optional)

Optional comma-separated domains to bypass proxy, for example ".com, chromium.org, .domain.com".

username str (optional)

Optional username to use if HTTP proxy requires authentication.

password str (optional)

Optional password to use if HTTP proxy requires authentication.

Network proxy settings.

slow_mo float (optional)#

Slows down Playwright operations by the specified amount of milliseconds. Useful so that you can see what is going on.

timeout float (optional)#

Maximum time in milliseconds to wait for the browser instance to start. Defaults to 30000 (30 seconds). Pass 0 to disable timeout.

traces_dir Union[str, pathlib.Path] (optional)#

If specified, traces are saved into this directory.

Returns

Browser#
launch_persistent_context
Added before v1.9
Returns the persistent browser context instance.

Launches browser that uses persistent storage located at user_data_dir and returns the only context. Closing this context will automatically close the browser.

Usage

browser_type.launch_persistent_context(user_data_dir)
browser_type.launch_persistent_context(user_data_dir, **kwargs)

Arguments

user_data_dir Union[str, pathlib.Path]#

Path to a User Data Directory, which stores browser session data like cookies and local storage. Pass an empty string to create a temporary directory.

More details for Chromium and Firefox. Chromium's user data directory is the parent directory of the "Profile Path" seen at chrome://version.

Note that browsers do not allow launching multiple instances with the same User Data Directory.

warning
Chromium/Chrome: Due to recent Chrome policy changes, automating the default Chrome user profile is not supported. Pointing userDataDir to Chrome's main "User Data" directory (the profile used for your regular browsing) may result in pages not loading or the browser exiting. Create and use a separate directory (for example, an empty folder) as your automation profile instead. See https://developer.chrome.com/blog/remote-debugging-port for details.

accept_downloads bool (optional)#

Whether to automatically download all the attachments. Defaults to true where all the downloads are accepted.

args List[str] (optional)#

warning
Use custom browser args at your own risk, as some of them may break Playwright functionality.

Additional arguments to pass to the browser instance. The list of Chromium flags can be found here.

base_url str (optional)#

When using page.goto(), page.route(), page.wait_for_url(), page.expect_request(), or page.expect_response() it takes the base URL in consideration by using the URL() constructor for building the corresponding URL. Unset by default. Examples:

baseURL: http://localhost:3000 and navigating to /bar.html results in http://localhost:3000/bar.html
baseURL: http://localhost:3000/foo/ and navigating to ./bar.html results in http://localhost:3000/foo/bar.html
baseURL: http://localhost:3000/foo (without trailing slash) and navigating to ./bar.html results in http://localhost:3000/bar.html
bypass_csp bool (optional)#

Toggles bypassing page's Content-Security-Policy. Defaults to false.

channel str (optional)#

Browser distribution channel.

Use "chromium" to opt in to new headless mode.

Use "chrome", "chrome-beta", "chrome-dev", "chrome-canary", "msedge", "msedge-beta", "msedge-dev", or "msedge-canary" to use branded Google Chrome and Microsoft Edge.

chromium_sandbox bool (optional)#

Enable Chromium sandboxing. Defaults to false.

client_certificates List[Dict] (optional) Added in: 1.46#

origin str

Exact origin that the certificate is valid for. Origin includes https protocol, a hostname and optionally a port.

certPath Union[str, pathlib.Path] (optional)

Path to the file with the certificate in PEM format.

cert bytes (optional)

Direct value of the certificate in PEM format.

keyPath Union[str, pathlib.Path] (optional)

Path to the file with the private key in PEM format.

key bytes (optional)

Direct value of the private key in PEM format.

pfxPath Union[str, pathlib.Path] (optional)

Path to the PFX or PKCS12 encoded private key and certificate chain.

pfx bytes (optional)

Direct value of the PFX or PKCS12 encoded private key and certificate chain.

passphrase str (optional)

Passphrase for the private key (PEM or PFX).

TLS Client Authentication allows the server to request a client certificate and verify it.

Details

An array of client certificates to be used. Each certificate object must have either both certPath and keyPath, a single pfxPath, or their corresponding direct value equivalents (cert and key, or pfx). Optionally, passphrase property should be provided if the certificate is encrypted. The origin property should be provided with an exact match to the request origin that the certificate is valid for.

Client certificate authentication is only active when at least one client certificate is provided. If you want to reject all client certificates sent by the server, you need to provide a client certificate with an origin that does not match any of the domains you plan to visit.

note
When using WebKit on macOS, accessing localhost will not pick up client certificates. You can make it work by replacing localhost with local.playwright.

color_scheme "light" | "dark" | "no-preference" | "null" (optional)#

Emulates prefers-colors-scheme media feature, supported values are 'light' and 'dark'. See page.emulate_media() for more details. Passing 'null' resets emulation to system defaults. Defaults to 'light'.

contrast "no-preference" | "more" | "null" (optional)#

Emulates 'prefers-contrast' media feature, supported values are 'no-preference', 'more'. See page.emulate_media() for more details. Passing 'null' resets emulation to system defaults. Defaults to 'no-preference'.

device_scale_factor float (optional)#

Specify device scale factor (can be thought of as dpr). Defaults to 1. Learn more about emulating devices with device scale factor.

devtools bool (optional)#

Deprecated
Use debugging tools instead.

Chromium-only Whether to auto-open a Developer Tools panel for each tab. If this option is true, the headless option will be set false.

downloads_path Union[str, pathlib.Path] (optional)#

If specified, accepted downloads are downloaded into this directory. Otherwise, temporary directory is created and is deleted when browser is closed. In either case, the downloads are deleted when the browser context they were created in is closed.

env Dict[str, str | float | bool] (optional)#

Specify environment variables that will be visible to the browser. Defaults to process.env.

executable_path Union[str, pathlib.Path] (optional)#

Path to a browser executable to run instead of the bundled one. If executable_path is a relative path, then it is resolved relative to the current working directory. Note that Playwright only works with the bundled Chromium, Firefox or WebKit, use at your own risk.

extra_http_headers Dict[str, str] (optional)#

An object containing additional HTTP headers to be sent with every request. Defaults to none.

firefox_user_prefs Dict[str, str | float | bool] (optional) Added in: v1.40#

Firefox user preferences. Learn more about the Firefox user preferences at about:config.

You can also provide a path to a custom policies.json file via PLAYWRIGHT_FIREFOX_POLICIES_JSON environment variable.

forced_colors "active" | "none" | "null" (optional)#

Emulates 'forced-colors' media feature, supported values are 'active', 'none'. See page.emulate_media() for more details. Passing 'null' resets emulation to system defaults. Defaults to 'none'.

geolocation Dict (optional)#

latitude float

Latitude between -90 and 90.

longitude float

Longitude between -180 and 180.

accuracy float (optional)

Non-negative accuracy value. Defaults to 0.

handle_sighup bool (optional)#

Close the browser process on SIGHUP. Defaults to true.

handle_sigint bool (optional)#

Close the browser process on Ctrl-C. Defaults to true.

handle_sigterm bool (optional)#

Close the browser process on SIGTERM. Defaults to true.

has_touch bool (optional)#

Specifies if viewport supports touch events. Defaults to false. Learn more about mobile emulation.

headless bool (optional)#

Whether to run browser in headless mode. More details for Chromium and Firefox. Defaults to true unless the devtools option is true.

http_credentials Dict (optional)#

username str

password str

origin str (optional)

Restrain sending http credentials on specific origin (scheme://host:port).

send "unauthorized" | "always" (optional)

This option only applies to the requests sent from corresponding APIRequestContext and does not affect requests sent from the browser. 'always' - Authorization header with basic authentication credentials will be sent with the each API request. 'unauthorized - the credentials are only sent when 401 (Unauthorized) response with WWW-Authenticate header is received. Defaults to 'unauthorized'.

Credentials for HTTP authentication. If no origin is specified, the username and password are sent to any servers upon unauthorized responses.

ignore_default_args bool | List[str] (optional)#

If true, Playwright does not pass its own configurations args and only uses the ones from args. If an array is given, then filters out the given default arguments. Dangerous option; use with care. Defaults to false.

ignore_https_errors bool (optional)#

Whether to ignore HTTPS errors when sending network requests. Defaults to false.

is_mobile bool (optional)#

Whether the meta viewport tag is taken into account and touch events are enabled. isMobile is a part of device, so you don't actually need to set it manually. Defaults to false and is not supported in Firefox. Learn more about mobile emulation.

java_script_enabled bool (optional)#

Whether or not to enable JavaScript in the context. Defaults to true. Learn more about disabling JavaScript.

locale str (optional)#

Specify user locale, for example en-GB, de-DE, etc. Locale will affect navigator.language value, Accept-Language request header value as well as number and date formatting rules. Defaults to the system default locale. Learn more about emulation in our emulation guide.

no_viewport bool (optional)#

Does not enforce fixed viewport, allows resizing window in the headed mode.

offline bool (optional)#

Whether to emulate network being offline. Defaults to false. Learn more about network emulation.

permissions List[str] (optional)#

A list of permissions to grant to all pages in this context. See browser_context.grant_permissions() for more details. Defaults to none.

proxy Dict (optional)#

server str

Proxy to be used for all requests. HTTP and SOCKS proxies are supported, for example http://myproxy.com:3128 or socks5://myproxy.com:3128. Short form myproxy.com:3128 is considered an HTTP proxy.

bypass str (optional)

Optional comma-separated domains to bypass proxy, for example ".com, chromium.org, .domain.com".

username str (optional)

Optional username to use if HTTP proxy requires authentication.

password str (optional)

Optional password to use if HTTP proxy requires authentication.

Network proxy settings.

record_har_content "omit" | "embed" | "attach" (optional)#

Optional setting to control resource content management. If omit is specified, content is not persisted. If attach is specified, resources are persisted as separate files and all of these files are archived along with the HAR file. Defaults to embed, which stores content inline the HAR file as per HAR specification.

record_har_mode "full" | "minimal" (optional)#

When set to minimal, only record information necessary for routing from HAR. This omits sizes, timing, page, cookies, security and other types of HAR information that are not used when replaying from HAR. Defaults to full.

record_har_omit_content bool (optional)#

Optional setting to control whether to omit request content from the HAR. Defaults to false.

record_har_path Union[str, pathlib.Path] (optional)#

Enables HAR recording for all pages into the specified HAR file on the filesystem. If not specified, the HAR is not recorded. Make sure to call browser_context.close() for the HAR to be saved.

record_har_url_filter str | Pattern (optional)#

record_video_dir Union[str, pathlib.Path] (optional)#

Enables video recording for all pages into the specified directory. If not specified videos are not recorded. Make sure to call browser_context.close() for videos to be saved.

record_video_size Dict (optional)#

width int

Video frame width.

height int

Video frame height.

Dimensions of the recorded videos. If not specified the size will be equal to viewport scaled down to fit into 800x800. If viewport is not configured explicitly the video size defaults to 800x450. Actual picture of each page will be scaled down if necessary to fit the specified size.

reduced_motion "reduce" | "no-preference" | "null" (optional)#

Emulates 'prefers-reduced-motion' media feature, supported values are 'reduce', 'no-preference'. See page.emulate_media() for more details. Passing 'null' resets emulation to system defaults. Defaults to 'no-preference'.

screen Dict (optional)#

width int

page width in pixels.

height int

page height in pixels.

Emulates consistent window screen size available inside web page via window.screen. Is only used when the viewport is set.

service_workers "allow" | "block" (optional)#

Whether to allow sites to register Service workers. Defaults to 'allow'.

'allow': Service Workers can be registered.
'block': Playwright will block all registration of Service Workers.
slow_mo float (optional)#

Slows down Playwright operations by the specified amount of milliseconds. Useful so that you can see what is going on.

strict_selectors bool (optional)#

If set to true, enables strict selectors mode for this context. In the strict selectors mode all operations on selectors that imply single target DOM element will throw when more than one element matches the selector. This option does not affect any Locator APIs (Locators are always strict). Defaults to false. See Locator to learn more about the strict mode.

timeout float (optional)#

Maximum time in milliseconds to wait for the browser instance to start. Defaults to 30000 (30 seconds). Pass 0 to disable timeout.

timezone_id str (optional)#

Changes the timezone of the context. See ICU's metaZones.txt for a list of supported timezone IDs. Defaults to the system timezone.

traces_dir Union[str, pathlib.Path] (optional)#

If specified, traces are saved into this directory.

user_agent str (optional)#

Specific user agent to use in this context.

viewport NoneType | Dict (optional)#

width int

page width in pixels.

height int

page height in pixels.

Sets a consistent viewport for each page. Defaults to an 1280x720 viewport. no_viewport disables the fixed viewport. Learn more about viewport emulation.

Returns

BrowserContext#
Properties
executable_path
Added before v1.9
A path where Playwright expects to find a bundled browser executable.

Usage

browser_type.executable_path

Returns

str#
name
Added before v1.9
Returns browser name. For example: 'chromium', 'webkit' or 'firefox'.

Usage

browser_type.name

Returns

str#
Previous
BrowserContext
Next
CDPSession
Methods
connect
connect_over_cdp
launch
launch_persistent_context
Properties
executable_path
name
Learn
Getting started
Playwright Training
Learn Videos
Feature Videos
Community
Stack Overflow
Discord
Twitter
LinkedIn
More
GitHub
YouTube
Blog
Ambassadors
Copyright © 2025 Microsoft





