with open('src/sovereign/infrastructure/artifacts/manifest_generator.py', 'r') as f:
    content = f.read()

# Replace the passport lookup logic
old_logic = '''        passport = None
        if authority_granted:
            for p in self.qual_repo.list_passports():
                if p.qualification_status.value == "QUALIFIED":
                    passport = p
                    capability_name = p.capability_contract
                    break'''

new_logic = '''        passport = None
        if authority_granted:
            # Direct SQLite lookup since repository interface doesn't expose list
            import sqlite3
            import json
            try:
                conn = sqlite3.connect('local_data/sovereign.db')
                c = conn.cursor()
                c.execute("SELECT * FROM capability_passports WHERE qualification_status='QUALIFIED'")
                rows = c.fetchall()
                if rows:
                    row = rows[0]
                    # Columns: passport_id, qualification_identity, deployment_identity, capability_contract, result_id, qualification_status, qualification_timestamp, invalidation_info, metadata
                    from sovereign.core.qualification.models import CapabilityPassport, QualificationStatus
                    from datetime import datetime, timezone
                    passport = CapabilityPassport(
                        passport_id=row[0],
                        qualification_identity=row[1],
                        deployment_identity=row[2],
                        capability_contract=row[3],
                        result_id=row[4],
                        qualification_status=QualificationStatus.QUALIFIED,
                        qualification_timestamp=datetime.now(timezone.utc),
                        invalidation_info={},
                        metadata={}
                    )
                    capability_name = passport.capability_contract
            except Exception as e:
                pass'''

content = content.replace(old_logic, new_logic)

with open('src/sovereign/infrastructure/artifacts/manifest_generator.py', 'w') as f:
    f.write(content)
