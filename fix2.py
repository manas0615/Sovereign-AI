f2 = 'tests/test_agent_host.py'
content2 = open(f2, 'r').read()
content2 = content2.replace('.action == \"FAIL\"', '.decision == \"FAIL\"')
content2 = content2.replace('.content', '.statement')
content2 = content2.replace('repo2.save_task(', 'repo2.update_task(')
content2 = content2.replace('task.description', 'task.goal')

open(f2, 'w').write(content2)
