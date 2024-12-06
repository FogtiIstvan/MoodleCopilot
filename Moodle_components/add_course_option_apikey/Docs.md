# Editing the course Logic to enable the entering of API keys.

This Documentation describes how I edited the course folder to enable the secure and controlled way of managing API Keys, that can be accessed only inside the courses. This solution requires the modification of core moodle codes.

## UI


I added the following snippet to the '/course/edit_form.php' file at line 411:

```
        $mform->addElement('header','LLM Options', get_string('LLM_header', 'qtype_automated_essay'));

        $mform->addElement('select', 'model',
                get_string('course_options_choose_model', 'qtype_automated_essay'),
                array(
                    '0' => 'GPT-4',
                    '1' => 'GPT-4o',
                    '2' => 'GPT-4o mini',
                    '3' => 'Mistral'
                ));

        $mform->setDefault('model', 'GPT-4');

        $mform->addElement('passwordunmask', 'apikey', get_string('course_options_add_apikey', 'qtype_automated_essay'));
        $mform->setType('apikey', PARAM_TEXT);

        $mform->addElement('text', 'llm_ip', get_string('course_options_add_ip', 'qtype_automated_essay'));
        $mform->setType('llm_ip', PARAM_TEXT);

        $mform->addElement('text', 'llm_port', get_string('course_options_add_port', 'qtype_automated_essay'));
        $mform->setType('llm_port', PARAM_TEXT);

        $mform->addElement('select', 'enableurls',
                get_string('course_options_enablesurls', 'qtype_automated_essay'),
                array(
                    '0' => get_string('no', 'qtype_automated_essay'),
                    '1' => get_string('yes', 'qtype_automated_essay')
                ));
        $mform->addHelpButton('enableurls', 'course_options_enablesurls', 'qtype_automated_essay');
        $mform->setDefault('enableurls', get_string('no', 'qtype_automated_essay'));

        
        $mform->addElement('select', 'enablefiles',
                get_string('course_options_enablefiles', 'qtype_automated_essay'),
                array(
                    '0' => get_string('no', 'qtype_automated_essay'),
                    '1' => get_string('yes', 'qtype_automated_essay')
                ));
        $mform->addHelpButton('enablefiles', 'course_options_enablefiles', 'qtype_automated_essay');
        $mform->setDefault('enablefiles', get_string('yes', 'qtype_automated_essay'));

```

This creates the UI elements in the course settings to insert the key.

## Adding Database table fields

I used the following queries to alter the mdl_course table and to add the two nessecary columns:

a.) 

```
ALTER TABLE mdl_course
ADD COLUMN model VARCHAR(255);

ALTER TABLE mdl_course
ADD COLUMN api_key TEXT;
```

and update the database

**OR**

b.)

go to /lib/db/install.xml

add the two fields to the course table.

```
        <FIELD NAME="model" TYPE="int" LENGTH="1"  NOTNULL="false" SEQUENCE="false"/>
        <FIELD NAME="apikey" TYPE="text" NOTNULL="false" SEQUENCE="false"/>
        <FIELD NAME="llm_ip" TYPE="text" NOTNULL="false" SEQUENCE="false"/>
        <FIELD NAME="llm_port" TYPE="text" NOTNULL="false" SEQUENCE="false"/>
        <FIELD NAME="enableurls" TYPE="int" LENGTH="1" NOTNULL="true" DEFAULT="0" SEQUENCE="false" COMMENT="1 = allow use of url resources for the LLM app. 0 = do not allow use of url resources for the LLM app."/>
        <FIELD NAME="enablefiles" TYPE="int" LENGTH="1" NOTNULL="true" DEFAULT="0" SEQUENCE="false" COMMENT="1 = allow use of file resources for the LLM app. 0 = do not allow use of file resources for the LLM app."/>
```

## Saving the values in the corresponding database field
