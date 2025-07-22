#!/usr/bin/env python3
"""
Check if required dependencies for system tray functionality are available
"""

def check_dependencies():
    print("🔍 Checking System Tray Dependencies...\n")
    
    # Check pystray and PIL
    try:
        import pystray
        print("✅ pystray: Available")
        pystray_version = getattr(pystray, '__version__', 'Unknown version')
        print(f"   Version: {pystray_version}")
    except ImportError as e:
        print("❌ pystray: Not available")
        print(f"   Error: {e}")
        print("   Install with: pip install pystray")
    
    try:
        from PIL import Image, ImageDraw
        print("✅ PIL (Pillow): Available")
        import PIL
        pil_version = getattr(PIL, '__version__', 'Unknown version')
        print(f"   Version: {pil_version}")
    except ImportError as e:
        print("❌ PIL (Pillow): Not available")
        print(f"   Error: {e}")
        print("   Install with: pip install Pillow")
    
    # Check win32 (optional)
    try:
        import win32gui
        import win32con
        print("✅ win32gui: Available (optional)")
    except ImportError as e:
        print("⚠️  win32gui: Not available (optional)")
        print("   This is optional for Windows taskbar integration")
        print("   Install with: pip install pywin32")
    
    print("\n" + "="*50)
    print("📋 SUMMARY:")
    print("="*50)
    
    # Check if system tray will work
    try:
        import pystray
        from PIL import Image, ImageDraw
        print("✅ System tray functionality: AVAILABLE")
        print("   You can use 'Hide to Background' with system tray icon")
    except ImportError:
        print("⚠️  System tray functionality: LIMITED")
        print("   'Hide to Background' will use taskbar minimization")
        print("   To enable full system tray, install: pip install pystray Pillow")
    
    print("\n🚀 Reminder App will work regardless!")
    print("   System tray is optional - taskbar minimization is the fallback")

if __name__ == "__main__":
    check_dependencies()
