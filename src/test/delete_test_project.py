from constants import PROJECT_DATA_REL_PATH, CONFIG_FILENAME
from project.project import ParallaxProject
import os

def delete_test_projects():
    project = ParallaxProject("testproject")
    project_dir = project.project_dir_path
    config_path = project.config_path
    if project.project_config_exists():
        os.remove(config_path)
    if project.project_dir_exists():
        os.rmdir(project_dir)
    assert not project.project_dir_exists()
    assert not project.project_config_exists()
    print("Test project deleted")