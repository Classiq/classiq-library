import sys
import re

#
# Defining single-line rules
#
def line_rule__allocate_with_size(line: str) -> str:
	"""
	Handling lines like:
		allocate(3, my_var)
	converting them into
		allocate(my_var.size, my_var)

	note: it doesn't know about the type of the variable (since it's stored in a different line)
		so it will also apply for types of size `QBit`, which is a bit embarassing to pass `var.size` for a qubit, which is of size 1
	"""
	if match := re.search("(allocate\\(\\d+\\s*,\\s*(\\S+)\\))", line):
		allocate_str, parameter_name = match.groups()
		line = line.replace(allocate_str, f"allocate({parameter_name}.size, {parameter_name})")

	return line


def line_rule__use_default_qnum(line: str) -> str:
	"""
	Handling lines like:
		QNUM[3, False, 0]
	converting them into:
		QNUM[3]
	"""
	for match in re.findall("(QNum\\[(\\d+)\\s*,\\s*False\\s*,\\s*0\\])", line):
		full_str, num_qubits = match
		line = line.replace(full_str, f"QNum[{num_qubits}]")

	return line


def line_rule__replace_prepare_int(line: str) -> str:
	"""
	Handling lines like:
		allocate(3, my_var)
	converting them into
		allocate(my_var.size, my_var)

	note: it doesn't know about the type of the variable (since it's stored in a different line)
		so it will also apply for types of size `QBit`, which is a bit embarassing to pass `var.size` for a qubit, which is of size 1
	"""
	if match := re.search("(inplace_prepare_int\\(\\s*(\\S+),\\s*(\\S+)\\))", line):
		allocate_str, expr, target_var = match.groups()
		line = line.replace(allocate_str, f"{target_var} ^= {expr}")

	return line


# small note: the first rule uses `re.search`, since it expects a single occurence
# and the second rule uses `re.findall`, since it expects multiple (or 0) occurences

LINE_BASED_RULES = [
	# line_rule__allocate_with_size,
	# line_rule__use_default_qnum,
	line_rule__replace_prepare_int,
]

#
# Defining multi-line rules (i.e. rules that take the whole file)
#
FILE_BASED_RULES = []

#
# Acting on files
#
def fix_file(file_path: str) -> None:
	with open(file_path) as f:
		file_data = f.read()

	# rules handling the full file
	for rule in FILE_BASED_RULES:
		file_data = rule(file_data)

	# files handling a single line:
	file_lines = file_data.splitlines()
	for rule in LINE_BASED_RULES:
		for index, line in enumerate(file_lines):
			file_lines[index] = rule(line)

	with open(file_path, 'w') as f:
		f.write('\n'.join(file_lines))
		f.write('\n')

def main() -> None:
	if len(sys.argv) < 2:
		print(f"Usage: {sys.argv[0]} file_path[, file_path[, ...]]")
		exit(1)

	for file in sys.argv[1:]:
		fix_file(file)

if __name__ == '__main__':
	main()
