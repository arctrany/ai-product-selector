1. 点击”开始任务“ 流程没有马上执行，而是卡在. 
   25-10-27 15:51:00,483 - src_new.workflow_engine.api.flow_routes - INFO - Started workflow abba-ccdd-eeff (latest version) with thread_id: thr_abdfb0218d0d4057
   INFO:     127.0.0.1:49437 - "POST /api/flows/abba-ccdd-eeff/start HTTP/1.1" 200 OK
   INFO:     ('127.0.0.1', 49460) - "WebSocket /api/runs/thr_abdfb0218d0d4057/events" [accepted]
   2025-10-27 15:51:00,511 - src_new.workflow_engine.api.workflow_ws - INFO - WebSocket connected for thread: thr_abdfb0218d0d4057
   INFO:     connection open

第二次点击"开始任务“后，才真正运行了流程引擎，但是没有立即输出日志。
我需要你检查点击‘开始任务’后的流程是否存在这个问题，给我解释为什么会出现这个现象。我的要求是‘开始任务’后任务立即运行，并且日志输出到控制台态，两者不能阻塞。