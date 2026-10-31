"""Tests only (never deployed: tools/): during the market's weekend the test servers run on Friday 15:00 ET (SWEEP_GAME_NOW,
tools/game-now.py); this puts the pages of the tests on that same time, so the app sees an open session there too (a trade
typed then goes to that session, 30 Oct., tour W1). Loaded by Python through PYTHONPATH=tools/clientclock (run.sh, par.py).
Each test starts at Friday 15:00 ET and its clock runs from there. A test that pins its own clock (clock.set_fixed_time,
window.__swNow) keeps it. Without SWEEP_GAME_NOW: nothing changes."""
import os, time
GN = os.environ.get('SWEEP_GAME_NOW', '')
if GN and not GN.startswith('@'):
  try:
    import datetime
    from zoneinfo import ZoneInfo
    at = datetime.datetime.strptime(GN, '%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo('America/New_York'))
    OFF = int(at.timestamp() * 1000 - time.time() * 1000)
    JS = """(() => { const off = %d, D = Date; if (globalThis.__swShift || globalThis.__swNoShift) return; globalThis.__swShift = off; globalThis.__swD = D;
      function S(...a) { if (!new.target) return new D(D.now() + off).toString(); return a.length ? new D(...a) : new D(D.now() + off); }
      S.prototype = D.prototype; S.now = () => D.now() + off; S.UTC = D.UTC; S.parse = D.parse; globalThis.Date = S; })()""" % OFF
    def patch(mod, is_async):
      B = mod.Browser
      nc, np = B.new_context, B.new_page
      if is_async:
        async def new_context(self, *a, **k):
          c = await nc(self, *a, **k); await c.add_init_script(JS); return c
        async def new_page(self, *a, **k):
          pg = await np(self, *a, **k); await pg.context.add_init_script(JS); return pg
      else:
        def new_context(self, *a, **k):
          c = nc(self, *a, **k); c.add_init_script(JS); return c
        def new_page(self, *a, **k):
          pg = np(self, *a, **k); pg.context.add_init_script(JS); return pg
      B.new_context, B.new_page = new_context, new_page
    import playwright.sync_api as _s, playwright.async_api as _a
    patch(_s, False); patch(_a, True)
    # a test that pins its own clock: the real Date back first, in its pages and the next ones
    UNDO = "globalThis.__swNoShift = 1; if (globalThis.__swD) globalThis.Date = globalThis.__swD"
    from playwright._impl._clock import Clock as _C
    def undo_first(orig):
      async def f(self, *a, **k):
        bc = self._browser_context
        if not getattr(bc, '_sw_off', False):
          bc._sw_off = True
          await bc.add_init_script(script=UNDO)
          for pg in bc.pages:
            try: await pg.evaluate(UNDO)
            except Exception: pass
        return await orig(self, *a, **k)
      return f
    for n in ('install', 'set_fixed_time', 'set_system_time', 'pause_at'):
      if hasattr(_C, n): setattr(_C, n, undo_first(getattr(_C, n)))
  except Exception:
    pass
