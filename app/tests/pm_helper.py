"""Tests: fill the pre-market questionnaire (the day's plan since the brief « Plan pre-market adaptatif ») with simple values.
A quiet day, the price inside the London range, the high watched (or the low: short=True); the max loss / max trades given
or the ones offered. sync: premarket(pg, ...); async: await apremarket(pg, ...). The sheet must already be open, or day= opens it; stop_at='limits' stops on that screen (call again to go on)."""
LEVELS = [('instrument', 'MES'), ('lv.london_high', '5820'), ('lv.london_low', '5800'), ('lv.pdh', '5850'), ('lv.pdl', '5770'), ('lv.price', '5810')]
SCREEN = "(document.querySelector('#gSheet.g-pm [data-pm-screen]') || {dataset: {}}).dataset.pmScreen || ''"

def premarket(pg, day=None, max_loss=None, max_trades=None, short=False, save=True, stop_at=None):
  if day is not None:
    pg.evaluate("(d) => SweepGame.openPlan(d)", day)
  for _ in range(60):
    if pg.evaluate(SCREEN): break
    pg.wait_for_timeout(150)
  for _ in range(12):
    s = pg.evaluate(SCREEN)
    if stop_at and s == stop_at: return True
    if s == 'base':
      for k, v in LEVELS: pg.fill(f'#gSheet [data-pmf="{k}"]', v)
    elif s == 'pos':
      if pg.locator('#gSheet [data-q="A2"]').count(): pg.click(f'#gSheet [data-q="A2"][data-v="{"low" if short else "high"}"]'); pg.wait_for_timeout(150)
    elif s == 'd1':
      if not pg.locator('#gSheet [data-q="D1"].on').count(): pg.click('#gSheet [data-q="D1"][data-v="gain"]'); pg.wait_for_timeout(150)
    elif s == 'limits':
      if pg.locator('#gSheet [data-q="D1_reduce"]').count(): pg.click('#gSheet [data-q="D1_reduce"][data-v="refuse"]'); pg.wait_for_timeout(150)
      if max_trades is not None: pg.fill('#gSheet [data-pmf="lim.max_trades"]', str(max_trades))
      if max_loss is not None: pg.fill('#gSheet [data-pmf="max_loss"]', str(max_loss))
      elif not pg.input_value('#gSheet [data-pmf="max_loss"]'): pg.fill('#gSheet [data-pmf="max_loss"]', '500')
    elif s == 'sheet':
      if save: pg.click('#gSheet [data-pm="save"]'); pg.wait_for_timeout(900)
      return True
    pg.click('#gSheet [data-pm="next"]'); pg.wait_for_timeout(250)
  return False

async def apremarket(pg, day=None, max_loss=None, max_trades=None, short=False, save=True, stop_at=None):
  if day is not None:
    await pg.evaluate("(d) => SweepGame.openPlan(d)", day)
  for _ in range(60):
    if await pg.evaluate(SCREEN): break
    await pg.wait_for_timeout(150)
  for _ in range(12):
    s = await pg.evaluate(SCREEN)
    if stop_at and s == stop_at: return True
    if s == 'base':
      for k, v in LEVELS: await pg.fill(f'#gSheet [data-pmf="{k}"]', v)
    elif s == 'pos':
      if await pg.locator('#gSheet [data-q="A2"]').count(): await pg.click(f'#gSheet [data-q="A2"][data-v="{"low" if short else "high"}"]'); await pg.wait_for_timeout(150)
    elif s == 'd1':
      if not await pg.locator('#gSheet [data-q="D1"].on').count(): await pg.click('#gSheet [data-q="D1"][data-v="gain"]'); await pg.wait_for_timeout(150)
    elif s == 'limits':
      if await pg.locator('#gSheet [data-q="D1_reduce"]').count(): await pg.click('#gSheet [data-q="D1_reduce"][data-v="refuse"]'); await pg.wait_for_timeout(150)
      if max_trades is not None: await pg.fill('#gSheet [data-pmf="lim.max_trades"]', str(max_trades))
      if max_loss is not None: await pg.fill('#gSheet [data-pmf="max_loss"]', str(max_loss))
      elif not await pg.input_value('#gSheet [data-pmf="max_loss"]'): await pg.fill('#gSheet [data-pmf="max_loss"]', '500')
    elif s == 'sheet':
      if save: await pg.click('#gSheet [data-pm="save"]'); await pg.wait_for_timeout(900)
      return True
    await pg.click('#gSheet [data-pm="next"]'); await pg.wait_for_timeout(250)
  return False
