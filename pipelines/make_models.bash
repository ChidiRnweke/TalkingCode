#! /bin/bash

# This script generates pydantic models for the github data from the json schemas


# NOTE: The generated models do need some editing to make them work as the schemas are not perfect
# and codegen seems to use an older version of pydantic. The AnyUrl type in particular is changed to
# a string type in the generated models. This is not a problem as the type doesn't do much in the
# generated models. On top of that, the `__root__` field is changed to the `root` field and `RootModel`
# is changed to `BaseModel` in the generated models for those that have it. This is because the `__root__`
# field is deprecated in the newer versions of pydantic.

source .venv/bin/activate
set -euxo pipefail
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

