
from project.project import ParallaxProject
from test.delete_test_project import delete_test_projects

def main():
    project = ParallaxProject("dresden")
    project.print_info()


if __name__ == "__main__":
    main()
    # delete_test_projects()