from project.project import ParallaxProject
from test.delete_test_project import delete_test_projects


def main():
    project_name = input("Enter the name of the project:\n> ")
    project = ParallaxProject(project_name)
    project.print_info()


if __name__ == "__main__":
    main()
    # delete_test_projects()
