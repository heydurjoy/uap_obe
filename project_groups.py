from typing import List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Student:
    name: str
    student_id: str
    email: str

class ProjectGroup:
    def __init__(self, group_number: int, project_name: str):
        self.group_number = group_number
        self.project_name = project_name
        self.students: List[Student] = []
        self.created_at = datetime.now()

    def add_student(self, student: Student) -> None:
        """Add a student to the group."""
        self.students.append(student)

    def remove_student(self, student_id: str) -> bool:
        """Remove a student from the group by their ID."""
        for i, student in enumerate(self.students):
            if student.student_id == student_id:
                self.students.pop(i)
                return True
        return False

    def get_student_count(self) -> int:
        """Get the number of students in the group."""
        return len(self.students)

    def is_valid(self) -> bool:
        """Check if the group has at least 2 students."""
        return len(self.students) >= 2

    def __str__(self) -> str:
        return f"Group {self.group_number} - {self.project_name} ({len(self.students)} students)"


class ProjectGroupManager:
    def __init__(self):
        self.groups: List[ProjectGroup] = []
        self.next_group_number = 1

    def create_group(self, project_name: str) -> ProjectGroup:
        """Create a new project group."""
        group = ProjectGroup(self.next_group_number, project_name)
        self.groups.append(group)
        self.next_group_number += 1
        return group

    def get_group(self, group_number: int) -> ProjectGroup:
        """Get a group by its number."""
        for group in self.groups:
            if group.group_number == group_number:
                return group
        raise ValueError(f"Group {group_number} not found")

    def remove_group(self, group_number: int) -> bool:
        """Remove a group by its number."""
        for i, group in enumerate(self.groups):
            if group.group_number == group_number:
                self.groups.pop(i)
                return True
        return False

    def get_all_groups(self) -> List[ProjectGroup]:
        """Get all project groups."""
        return self.groups

    def get_invalid_groups(self) -> List[ProjectGroup]:
        """Get all groups that have fewer than 2 students."""
        return [group for group in self.groups if not group.is_valid()]


# Example usage
if __name__ == "__main__":
    # Create a project group manager
    manager = ProjectGroupManager()

    # Create some students
    student1 = Student("John Doe", "S001", "john@example.com")
    student2 = Student("Jane Smith", "S002", "jane@example.com")
    student3 = Student("Bob Johnson", "S003", "bob@example.com")

    # Create a project group
    group = manager.create_group("Web Development Project")
    
    # Add students to the group
    group.add_student(student1)
    group.add_student(student2)
    group.add_student(student3)

    # Print group information
    print(group)
    print(f"Number of students: {group.get_student_count()}")
    print(f"Is valid group: {group.is_valid()}")

    # Remove a student
    group.remove_student("S002")
    print(f"\nAfter removing a student:")
    print(group)
    print(f"Number of students: {group.get_student_count()}")
    print(f"Is valid group: {group.is_valid()}") 