import contextvars

from .crypto_trading import main

if __name__ == "__main__":
    ctx = contextvars.copy_context()
    try:
        ctx.run(main())
    except KeyboardInterrupt:
        pass
