import contextvars
import os

from .crypto_trading import main

if __name__ == "__main__":
    ctx = contextvars.copy_context()
    try:
        ctx.run(main())
    except TypeError:
        os._exit(1)
    except KeyboardInterrupt:
        pass
