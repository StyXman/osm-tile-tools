all: project.mml style.mss

project_input=$(wildcard input/*.mml)

project.mml: $(project_input)
	./generate_project.sh

style_input=$(wildcard input/*.mss)

style.mss: $(style_input)
	./generate_style.sh
