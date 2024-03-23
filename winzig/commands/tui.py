import asyncio
import click
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.tui import TuiApp


@click.command(
    name="tui",
    help="Start a TUI for interacting with the search engine.",
)
@click.pass_context
def start_tui(ctx):
    asyncio.run(_start_tui(ctx.obj["engine"]))


async def _start_tui(engine):
    async with AsyncSession(engine) as session:
        tui_app = TuiApp(session, k1=1.5, b=0.75)
        await tui_app.run_async()
