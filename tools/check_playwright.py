try:
    from playwright.sync_api import sync_playwright
    print('sync_playwright OK')
except Exception as e:
    print('IMPORT_ERROR', e)
