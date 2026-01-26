from setuptools import setup, find_packages

# Bench installs apps in editable mode; keep setup.py minimal and stable.

setup(
    name="alphax_card_terminal",
    version="0.0.5",
    description="Card terminal metadata capture framework (MoP-driven) for ERPNext/Frappe.",
    author="AlphaX",
    author_email="support@alphax.com",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
