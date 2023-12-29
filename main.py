from base64 import b64decode
from io import BytesIO
from os import path
from time import sleep

import dearpygui.dearpygui as dpg
import requests
import yaml
from PIL import Image

from src.utils.nodes import NodeParent, theme
from src.utils.view import toaster

cookey = True


class Inference:  # Crunchy Moon AI Inference
    def __init__(self):
        pass

    def refactoring(self, original):
        return original.replace(b"data:image/png;base64,", b"")

    def decompiller_processor(self, compilled_data: str):
        """Decompile the generated image and change to PIL object"""
        try:
            binary_data: bytes = b64decode(compilled_data)
        except Exception as e:
            toaster.show("Decompiller processor got an error", f"{e}")
        return Image.open(BytesIO(binary_data))

    def ImagineA(self, prompt: str, modelID: str, fileID: str, negative: str):
        global cookey
        p = requests.post(
            "https://swiftysbetatestapi.vercel.app/imagine",
            json={
                "prompt": prompt,
                "modelId": modelID,
                "modelFileId": fileID,
                "negative": negative,
            },
        )
        cookey = False
        while True:
            try:
                x = requests.post(
                    "https://swiftysbetatestapi.vercel.app/check_status",
                    json={"encrypted_data": p.content.decode("utf-8")},
                )
                print(x.content)
                if x.json()["status"] == "Completed":
                    print("Success! Breaking out of the loop.")
                    image_url = x.json()["image_url"]
                    crescent = image_url.encode("utf-8")
                    refactored = self.refactoring(crescent)
                    del image_url, crescent
                    cookey = True
                    return self.decompiller_processor(refactored)

                sleep(5)
            except Exception as e:
                toaster.show(
                    "Error on API",
                    f"An error occured while trying to imagine your prompt. {e}",
                )


class Node(NodeParent):
    def __init__(self):
        # We load some universal variables from NodeParent that every node uses
        super().__init__()

        with open(path.dirname(__file__) + "/plugin.yaml") as file:
            self.info = yaml.safe_load(file)

        self.name = self.info["name"]
        self.tooltip = self.info["description"]

        # PLUGINS VARIABLES
        self.predefined_negative_options = [
            "Lite Humanoid negative",
            "Default humanoid negative",
            "Custom",
        ]
        self.model_options = ["Realist - Humanoid", "Anime - NSFW", "Anime", "Animal"]

    def new(self, history=True):
        # This is where you create the node using dearpygui
        with dpg.node(
            parent="MainNodeEditor",
            tag=self.name + "_" + str(self.counter),
            label=self.name,
            user_data=self,
        ):
            dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Input)
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_input_text(
                    tag=self.name + "_prompt_" + str(self.counter),
                    label="Prompt",
                    multiline=True,
                    width=400,
                    height=200,
                    default_value="",
                    callback=self.update_output,
                )

                # Model choice
                dpg.add_combo(
                    tag=self.name + "_model_" + str(self.counter),
                    label="Choose a model",
                    items=self.model_options,
                    default_value="Realist - Humanoid",
                    width=400,
                    callback=self.update_output,
                )

                # Negative predefined choice
                dpg.add_combo(
                    tag=self.name + "_predefined_negative_" + str(self.counter),
                    label="Choose a model",
                    items=self.predefined_negative_options,
                    default_value="Default humanoid negative",
                    width=400,
                    callback=self.update_output,
                )

                # Custom negative prompt
                dpg.add_input_text(
                    label="Negatives",
                    multiline=True,
                    width=400,
                    height=200,
                    tag=self.name + "_negative_" + str(self.counter),
                    callback=self.update_output,
                )

                # Generate button
                dpg.add_button(
                    label="Generate",
                    callback=self.button_gen,
                )

        tag = self.name + "_" + str(self.counter)

        # You can provide an optional theme to the node
        dpg.bind_item_theme(tag, theme.yellow)
        # This is where you store the settings; they get automatically updated when the user changes them
        self.settings[tag] = {
            self.name + "_prompt_" + str(self.counter): "",
            self.name + "_model_" + str(self.counter): "Realist - Humanoid",
            self.name
            + "_predefined_negative_"
            + str(self.counter): "Default humanoid negative",
            self.name + "_negative_" + str(self.counter): "",
        }
        # This is a boilerplate function that should be called at the end to make it work with the history
        self.end(tag, history)
        print(self.settings)

    def button_gen(self):
        tag = self.name + "_" + str(self.counter - 1)
        current_prompt = self.settings[tag][
            self.name + "_prompt_" + str(self.counter - 1)
        ]
        current_model = self.settings[tag][
            self.name + "_model_" + str(self.counter - 1)
        ]
        current_negative = self.settings[tag][
            self.name + "_negative_" + str(self.counter - 1)
        ]
        current_predefined_negative = self.settings[tag][
            self.name + "_predefined_negative_" + str(self.counter - 1)
        ]

        # Predefined negative handling
        if current_predefined_negative == "Lite Humanoid negative":
            current_negative = "extra limbs, extra fingers, distorted face, asymmetrical eyes, writing, distorted ears, bad anatomy"
        elif current_predefined_negative == "Default humanoid negative":
            current_negative = """EasyNegative, badhandv4, watermark, signature, username, text, make up, bad quality, 
                                low quality, (missing hands, missing legs, missing finger), (extra hands, extra legs, extra finger), 
                                (bad hands, bad legs, bad finger), simple background, greyscale, monochrome, duplicate, mutilated, mutated, 
                                mutation, deformed, poorly drawn hands, poorly drawn face, malformed limbs, extra limbs, cloned face, disfigured, 
                                logo, signature, animal, object"""
        elif current_predefined_negative == "Custom":
            pass

        # Model handling
        if current_model == "Realist - Humanoid":
            file_id = 643802146102442091
            model_id = 643802146103490665
        elif current_model == "Anime - NSFW":
            file_id = 660463028618340500
            model_id = 660101920654080997
        elif current_model == "Anime":
            file_id = 645300814810711493
            model_id = 645300814811760068
        elif current_model == "Animal":
            file_id = 662883732315746312
            model_id = 662883732316794887

        if cookey:
            answer = Inference().ImagineA(
                current_prompt, model_id, file_id, current_negative
            )
            self.run(answer, tag=tag)
        else:
            pass

    def run(self, image: Image, tag: str) -> Image:
        print(image)
        return image
