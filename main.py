import shortly.shortly

app = shortly.shortly.create_app()
shortly.shortly.run_simple("127.0.0.1", 5000, app, use_debugger=True, use_reloader=True)