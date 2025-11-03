"""
Browser Fingerprinting Randomization Module
Implements comprehensive anti-fingerprinting techniques to make each browser session unique
"""
import random


def get_random_user_agent():
    """Returns a random, realistic, up-to-date user agent string"""

    # Latest Chrome versions (2024-2025)
    chrome_versions = [
        "130.0.6723.92", "130.0.6723.116", "131.0.6778.69", "131.0.6778.85",
        "129.0.6668.100", "129.0.6668.89", "128.0.6613.138", "128.0.6613.120"
    ]

    # Windows versions with realistic distribution
    windows_versions = [
        "Windows NT 10.0; Win64; x64",  # Windows 10/11
        "Windows NT 10.0; WOW64",
        "Windows NT 10.0",
    ]

    # WebKit versions that match Chrome versions
    webkit_versions = [
        "537.36"
    ]

    chrome_ver = random.choice(chrome_versions)
    win_ver = random.choice(windows_versions)
    webkit_ver = random.choice(webkit_versions)

    user_agents = [
        f"Mozilla/5.0 ({win_ver}) AppleWebKit/{webkit_ver} (KHTML, like Gecko) Chrome/{chrome_ver} Safari/{webkit_ver}",
        f"Mozilla/5.0 ({win_ver}) AppleWebKit/{webkit_ver} (KHTML, like Gecko) Chrome/{chrome_ver} Safari/{webkit_ver} Edg/{chrome_ver}",
    ]

    return random.choice(user_agents)


def get_random_screen_resolution():
    """Returns a random but realistic screen resolution"""
    common_resolutions = [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1600, 900),
        (1280, 720),
        (1280, 800),
        (2560, 1440),
        (1680, 1050),
        (1920, 1200),
    ]
    return random.choice(common_resolutions)


def get_random_viewport_size(screen_width, screen_height):
    """Returns a realistic viewport size based on screen resolution"""
    # Subtract typical browser chrome (toolbars, etc.)
    width = screen_width
    height = screen_height - random.randint(100, 150)
    return (width, height)


def get_random_timezone():
    """Returns a random timezone offset"""
    timezones = [
        "America/New_York",
        "America/Chicago",
        "America/Los_Angeles",
        "America/Denver",
        "Europe/London",
        "Europe/Paris",
        "Europe/Berlin",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Australia/Sydney",
    ]
    return random.choice(timezones)


def get_random_language():
    """Returns a random language setting"""
    languages = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.9,es;q=0.8",
        "en-US,en;q=0.9,fr;q=0.8",
        "en-US,en;q=0.9,de;q=0.8",
    ]
    return random.choice(languages)


def get_random_platform():
    """Returns a random platform string"""
    platforms = [
        "Win32",
        "Win64",
    ]
    return random.choice(platforms)


def get_random_hardware_concurrency():
    """Returns a random CPU core count"""
    return random.choice([2, 4, 6, 8, 12, 16])


def get_random_device_memory():
    """Returns a random device memory in GB"""
    return random.choice([2, 4, 8, 16, 32])


def get_anti_fingerprint_script():
    """
    Returns a comprehensive JavaScript snippet that randomizes browser fingerprinting vectors
    This prevents Canvas, WebGL, Audio fingerprinting, and more
    """

    hw_concurrency = get_random_hardware_concurrency()
    device_memory = get_random_device_memory()
    platform = get_random_platform()

    # Generate random noise for canvas fingerprinting
    canvas_noise = random.uniform(0.0001, 0.001)

    script = f"""
    // Anti-fingerprinting script
    
    // 1. Override hardware concurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {hw_concurrency}
    }});
    
    // 2. Override device memory
    Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => {device_memory}
    }});
    
    // 3. Override platform
    Object.defineProperty(navigator, 'platform', {{
        get: () => '{platform}'
    }});
    
    // 4. Canvas fingerprinting protection - add noise to canvas operations
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const originalToBlob = HTMLCanvasElement.prototype.toBlob;
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    
    // Add noise to canvas
    const addCanvasNoise = (imageData) => {{
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {{
            data[i] = data[i] + Math.floor(Math.random() * {canvas_noise} * 255);
            data[i+1] = data[i+1] + Math.floor(Math.random() * {canvas_noise} * 255);
            data[i+2] = data[i+2] + Math.floor(Math.random() * {canvas_noise} * 255);
        }}
        return imageData;
    }};
    
    HTMLCanvasElement.prototype.toDataURL = function() {{
        const context = this.getContext('2d');
        if (context) {{
            const imageData = context.getImageData(0, 0, this.width, this.height);
            addCanvasNoise(imageData);
            context.putImageData(imageData, 0, 0);
        }}
        return originalToDataURL.apply(this, arguments);
    }};
    
    CanvasRenderingContext2D.prototype.getImageData = function() {{
        const imageData = originalGetImageData.apply(this, arguments);
        return addCanvasNoise(imageData);
    }};
    
    // 5. WebGL fingerprinting protection
    const getParameterOriginal = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        // Randomize WebGL parameters
        if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
            return 'Intel Inc.';
        }}
        if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL
            const renderers = ['Intel Iris OpenGL Engine', 'Intel HD Graphics', 'ANGLE (Intel)'];
            return renderers[Math.floor(Math.random() * renderers.length)];
        }}
        return getParameterOriginal.apply(this, arguments);
    }};
    
    // Also for WebGL2
    if (typeof WebGL2RenderingContext !== 'undefined') {{
        const getParameterOriginal2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) {{ return 'Intel Inc.'; }}
            if (parameter === 37446) {{
                const renderers = ['Intel Iris OpenGL Engine', 'Intel HD Graphics', 'ANGLE (Intel)'];
                return renderers[Math.floor(Math.random() * renderers.length)];
            }}
            return getParameterOriginal2.apply(this, arguments);
        }};
    }}
    
    // 6. Audio fingerprinting protection
    const audioContext = window.AudioContext || window.webkitAudioContext;
    if (audioContext) {{
        const OriginalAnalyser = audioContext.prototype.createAnalyser;
        audioContext.prototype.createAnalyser = function() {{
            const analyser = OriginalAnalyser.apply(this, arguments);
            const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
            analyser.getFloatFrequencyData = function(array) {{
                originalGetFloatFrequencyData.apply(this, arguments);
                // Add noise to audio data
                for (let i = 0; i < array.length; i++) {{
                    array[i] = array[i] + Math.random() * 0.1;
                }}
            }};
            return analyser;
        }};
    }}
    
    // 7. Battery API - return undefined to prevent tracking
    Object.defineProperty(navigator, 'getBattery', {{
        get: () => undefined
    }});
    
    // 8. Media devices - reduce fingerprinting surface
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
        const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
        navigator.mediaDevices.enumerateDevices = function() {{
            return originalEnumerateDevices.apply(this, arguments).then(devices => {{
                // Return generic devices
                return devices.map(device => ({{
                    deviceId: 'default',
                    kind: device.kind,
                    label: '',
                    groupId: 'default'
                }}));
            }});
        }};
    }}
    
    // 9. Plugins - return empty to avoid fingerprinting
    Object.defineProperty(navigator, 'plugins', {{
        get: () => []
    }});
    
    // 10. Screen orientation randomization
    if (window.screen && window.screen.orientation) {{
        Object.defineProperty(window.screen.orientation, 'type', {{
            get: () => 'landscape-primary'
        }});
    }}
    
    // 11. Remove Selenium/WebDriver indicators
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined
    }});
    
    // 12. Permissions API - prevent fingerprinting via permissions
    if (navigator.permissions && navigator.permissions.query) {{
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = function(parameters) {{
            return originalQuery.apply(this, arguments).then(result => {{
                Object.defineProperty(result, 'state', {{
                    get: () => 'prompt'
                }});
                return result;
            }});
        }};
    }}
    
    // 13. Font fingerprinting protection - limit exposed fonts
    if (document.fonts && document.fonts.check) {{
        const originalCheck = document.fonts.check;
        document.fonts.check = function() {{
            // Always return true for common fonts
            return true;
        }};
    }}
    
    // 14. Timezone randomization is handled by Chrome arguments
    
    // 15. Connection API - prevent network info fingerprinting
    if (navigator.connection) {{
        Object.defineProperty(navigator, 'connection', {{
            get: () => ({{
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false
            }})
        }});
    }}
    
    // 16. Do Not Track - randomize
    Object.defineProperty(navigator, 'doNotTrack', {{
        get: () => null
    }});
    
    console.log('[Anti-Fingerprint] Protection activated');
    """

    return script


def get_chrome_options_with_randomization():
    """
    Returns Chrome options with comprehensive anti-fingerprinting settings
    """
    options = []

    # 1. User agent is set separately via CDP

    # 2. Disable automation flags
    options.extend([
        '--disable-blink-features=AutomationControlled',
        '--disable-features=IsolateOrigins,site-per-process',
    ])

    # 3. Randomize window size
    screen_width, screen_height = get_random_screen_resolution()
    options.append(f'--window-size={screen_width},{screen_height}')

    # 4. Language randomization
    lang = get_random_language().split(',')[0]
    options.append(f'--lang={lang}')

    # 5. Disable WebRTC (can leak real IP)
    options.extend([
        '--disable-webrtc',
        '--disable-webrtc-hw-encoding',
        '--disable-webrtc-hw-decoding',
    ])

    # 6. Disable various tracking/fingerprinting features
    options.extend([
        '--disable-features=AudioServiceOutOfProcess',
        '--disable-background-networking',
        '--disable-default-apps',
        '--disable-extensions',
        '--disable-sync',
        '--disable-translate',
        '--disable-notifications',
    ])

    # 7. Canvas fingerprinting - handled by JavaScript injection

    # 8. Timezone randomization
    timezone = get_random_timezone()
    options.append(f'--timezone={timezone}')

    # 9. Disable GPU for WebGL consistency (can re-enable if needed)
    # Comment out if you need WebGL performance
    # options.append('--disable-gpu')

    # 10. Additional privacy options
    options.extend([
        '--no-first-run',
        '--no-service-autorun',
        '--password-store=basic',
        '--use-mock-keychain',
        '--disable-component-update',
    ])

    # 11. Disable save password prompts
    options.append('--disable-save-password-bubble')

    # 12. Memory cache randomization (affects ETag)
    options.append(f'--disk-cache-size={random.randint(50000000, 100000000)}')

    # 13. TLS/SSL fingerprinting mitigation
    # Chrome uses BoringSSL which has consistent fingerprints, but we can randomize cipher order
    # This is limited in Chrome, but we disable some features
    options.extend([
        '--disable-features=EnableTLS13EarlyData',
    ])

    return options


def apply_cdp_anti_fingerprint(driver):
    """
    Apply Chrome DevTools Protocol commands to further randomize fingerprint
    Must be called after driver initialization
    """

    # 1. Override user agent
    user_agent = get_random_user_agent()
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": user_agent,
        "platform": get_random_platform(),
        "acceptLanguage": get_random_language()
    })

    # 2. Set timezone
    timezone = get_random_timezone()
    driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
        'timezoneId': timezone
    })

    # 3. Set locale
    driver.execute_cdp_cmd('Emulation.setLocaleOverride', {
        'locale': get_random_language().split(',')[0]
    })

    # 4. Inject anti-fingerprinting script
    script = get_anti_fingerprint_script()
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': script
    })

    # 5. Disable cache to prevent ETag tracking
    driver.execute_cdp_cmd('Network.setCacheDisabled', {'cacheDisabled': True})

    # 6. Clear cookies and cache
    driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
    driver.execute_cdp_cmd('Network.clearBrowserCache', {})

    return user_agent


def get_random_window_size():
    """Returns randomized window size based on screen resolution"""
    screen_width, screen_height = get_random_screen_resolution()
    viewport_width, viewport_height = get_random_viewport_size(screen_width, screen_height)
    return viewport_width, viewport_height
