TypeError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/combat-aircraft-fleet-availability-simulator/fleet-dashboard/app.py", line 100, in <module>
    result = cached_single_run(
             ^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.11/site-packages/streamlit/runtime/caching/cache_utils.py", line 281, in __call__
    return self._get_or_create_cached_value(args, kwargs, spinner_message)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.11/site-packages/streamlit/runtime/caching/cache_utils.py", line 326, in _get_or_create_cached_value
    return self._handle_cache_miss(cache, value_key, func_args, func_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.11/site-packages/streamlit/runtime/caching/cache_utils.py", line 385, in _handle_cache_miss
    computed_value = self._info.func(*func_args, **func_kwargs)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/mount/src/combat-aircraft-fleet-availability-simulator/fleet-dashboard/utils/cache_manager.py", line 16, in cached_single_run
    r = run_single(
        ^^^^^^^^^^^
File "/mount/src/combat-aircraft-fleet-availability-simulator/fleet-dashboard/simulation/engine.py", line 320, in run_single
    env.run(until=sim_days * HOURS_PER_DAY)
File "/home/adminuser/venv/lib/python3.11/site-packages/simpy/core.py", line 246, in run
    self.step()
File "/home/adminuser/venv/lib/python3.11/site-packages/simpy/core.py", line 204, in step
    raise exc