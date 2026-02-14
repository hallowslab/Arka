import os
import toml

pyproject_path = "pyproject.toml"
pyproject = toml.load(pyproject_path)

# Map env vars to groups and branches
group_map = {
    "PYMAP_ENABLED": ("pymap", "modularize"),  # (group_name, branch)
    "AERA_ENABLED": ("aera", "dev"),
}

for env_var, (group_name, branch) in group_map.items():
    group = (
        pyproject.get("tool", {}).get("poetry", {}).get("group", {}).get(group_name, {})
    )
    if not group:
        print(f"Group {group_name} does not exist!")
        continue  # skip if group does not exist

    # Check if env var is set to true
    print(
        f"Variable {env_var} is True? {os.environ.get(env_var, "false").lower() == "true"}"
    )
    if os.environ.get(env_var, "false").lower() == "true":
        for _, spec in group.items():
            for name, props in spec.items():
                if isinstance(props, dict) and "git" in props:
                    # Update branch in properties of the dependency spec
                    print(
                        f"Updating branch for {name} from {props['branch']} to {branch}"
                    )
                    props["branch"] = branch
    else:
        # Optionally, we could remove the dependency entirely if env var is false
        # pyproject["tool"]["poetry"]["group"][group_name] = {}
        continue

# Write changes back to pyproject.toml
with open(pyproject_path, "w") as f:
    toml.dump(pyproject, f)

print("Poetry groups updated based on environment variables")
