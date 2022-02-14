import sys
from IPython import embed

from pdf12step.templating import Context


def main():
    context = Context({})
    config = context.config
    meetings = context.get_meetings()
    ctx = sys.modules['__main__'].__dict__
    ctx.update(locals())
    embed(colors='linux', module=sys.modules['__main__'], user_ns=ctx)


if __name__ == '__main__':
    main()
