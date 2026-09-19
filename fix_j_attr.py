with open('exp_j_suite.py', 'r') as f:
    content = f.read()

content = content.replace("profile_orig = svc.deployment_profiles.get", "profile_orig = svc.router.deployment_profiles.get")

with open('exp_j_suite.py', 'w') as f:
    f.write(content)
