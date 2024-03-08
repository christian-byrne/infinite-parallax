from project.project import ParallaxProject
from test.delete_test_project import delete_test_projects
from constants import DEV
import os


if __name__ == "__main__":
    if DEV:
        os.system("clear")
    project_name = input("\nEnter the name of the project:\n> ")
    print("\n")
    project = ParallaxProject(project_name)
    # delete_test_projects()
