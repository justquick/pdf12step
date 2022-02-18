import sys

from pdf12step.templating import Context


def main(args={}):
    from IPython import embed
    context = Context(args)
    config = context.config
    meetings = context.get_meetings()
    ctx = sys.modules['__main__'].__dict__
    ctx.update(locals())
    embed(colors='linux', module=sys.modules['__main__'], user_ns=ctx)


if __name__ == '__main__':
    main()
