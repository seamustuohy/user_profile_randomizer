# User Profile Randomizer
Randomizes the gender pronoun, name (chosen from a random language family), and photo on a set of user personas.

In an effort to combat the inclusion of possible implicit biases an author might hold based upon the nationality, race, or gender of the personas that they write this library allows for more neutral user persona templates to be seeded with randomized name (chosen from a random language family), gender pronouns, and photos.

To do this user persona templates are created using placeholders for the personas name (name, full name), and gender pronouns (xey,xem,xyr,xyrs,xemself).

The randomization process used software to:
1. choose randomly between male and female;
2. request a random language from WikiData that has given names associated with that gender;
3. request a random given name and family name from WikiData that match the chosen gender and languages;
4. check to ensure that the name does not belong to any existing person on WikiData; and
5. select a photo that corresponds to the chosen gender from a library of appropriately licensed profile photos.


# Running Profile Creator

Here is a command to use the examples that are provided.

```sh
python3 profile.py -v -p examples/profiles/ \
                      -c examples/converted/ \
                      -l examples/license.csv \
                      -i examples/images/ \
                      -t examples/templates/basic.tex \
                      -o examples/output/
```

To convert a whole folder of profiles
```sh
python3 profile.py --verbose --profile profiles/ \
                             --converted converted_profiles/ \
                             --license_path license.csv \
                             --image_path photos/ \
                             --template_path templates/basic.tex \
                             --output_directory output/
```

To convert a single profile
```sh
python3 profile.py --verbose --profile profiles/001.md \
                             --converted converted_profiles/001.md \
                             --license_path license.csv \
                             --image_path photos \
                             --template_path templates/basic.tex \
                             --output_directory output/
```
