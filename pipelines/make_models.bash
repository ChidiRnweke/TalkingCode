source .venv/bin/activate
input_folder="github_input_schemas"
output_folder="src/talkingcode/pipelines/github_models"

generate_model() {
    local input_file=$1
    local output_file=$2

    if [ ! -f "${output_file}" ]; then
        datamodel-codegen --input ${input_file} --input-file-type jsonschema --output ${output_file}
    fi
}

generate_model "${input_folder}/user_repositories.json" "${output_folder}/repositories.py"
generate_model "${input_folder}/git_files.json" "${output_folder}/files.py"
generate_model "${input_folder}/repository_content.json" "${output_folder}/file_content.py"
generate_model "${input_folder}/user.json" "${output_folder}/user.py"
generate_model "${input_folder}/repository_languages.json" "${output_folder}/languages.py"

