import click
from click_repl import repl, ExitReplException
from prompt_toolkit.history import FileHistory

from plugins import picture_extractor

CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    obj={},
)

@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
def main():
    ctx = click.get_current_context()
    return

main.add_command(picture_extractor.pic)

@main.command()
def term():
    """Open the application in terminal mode."""
    prompt_kwargs = {
        'history': FileHistory('./.myrepl-history'),
    }
    ctx = click.get_current_context()
    repl(ctx, prompt_kwargs=prompt_kwargs)

@main.command(name="help")
def help_():
    """Print help message."""
    click.echo(main.get_help(click.get_current_context()))

@main.command(name="quit")
def q():
    """Quit the terminal and exit the app."""
    raise ExitReplException()

if __name__ == "__main__":
    main(max_content_width=120)
