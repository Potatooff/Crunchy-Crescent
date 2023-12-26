from base64 import b64decode
from io import BytesIO
from os import listdir, path
from time import sleep

import dearpygui.dearpygui as dpg
import requests
import yaml
from PIL import Image

from src.utils import ImageController as dpg_img
from src.utils.nodes import NodeParent, theme
from src.utils.paths import resource


class Inference:  # Crunchy Moon AI Inference
    def __init__(self):
        pass

    def refactoring(self, original):
        return original.replace(b"data:image/png;base64,", b"")

    def decompiller_processor(self, compilled_data: str):
        """Decompile the generated image and change to PIL object"""
        binary_data: bytes = b64decode(compilled_data)
        return Image.open(BytesIO(binary_data))

    def ImagineA(self, prompt: str, modelID: str, fileID: str, negative: str):
        p = requests.post(
            "https://swiftysbetatestapi.vercel.app/imagine",
            json={
                "prompt": prompt,
                "modelId": modelID,
                "modelFileId": fileID,
                "negative": negative,
            },
        )
        while True:
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
                return self.decompiller_processor(refactored)

            sleep(5)


class Node(NodeParent):
    def __init__(self):
        # We load some universal variables from NodeParent that every node uses
        super().__init__()

        with open(path.dirname(__file__) + "/plugin.yaml") as file:
            self.info = yaml.safe_load(file)

        self.name = self.info["name"]
        self.tooltip = self.info["description"]
        self.viewer = None
        self.image = ""
        self.protected = True
        self.image_path = ""

        # options
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
            # I made this node output only
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                # Prompt + tooltips
                dpg.add_input_text(
                    tag=self.name + "_prompt_" + str(self.counter),
                    label="Prompt",
                    multiline=True,
                    width=400,
                    height=200,
                    default_value="",
                    callback=self.update_output,
                )
                with dpg.tooltip(self.name + "_prompt_" + str(self.counter)):
                    dpg.add_text(
                        "Write down a prompt. Ex: A cat in the forest, add details to make it more accurate."
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
                with dpg.tooltip(self.name + "_model_" + str(self.counter)):
                    dpg.add_text(
                        "Choose a model to fit the perfect task for your generation."
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
                with dpg.tooltip(
                    self.name + "_predefined_negative_" + str(self.counter)
                ):
                    dpg.add_text(
                        "These are predefined negative prompts. It will override the negative prompt text box."
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
                with dpg.tooltip(self.name + "_negative_" + str(self.counter)):
                    dpg.add_text(
                        "Write down what you dont want to be generated. Ex: A dog."
                    )

                # self.viewer = dpg_img.add_image(self.image)

                # Generate button + Status

        tag = self.name + "_" + str(self.counter)

        # You can provide an optional theme to the node
        dpg.bind_item_theme(tag, theme.yellow)
        # This is where you store the settings; they get automatically updated when the user changes them
        self.settings[tag] = {
            self.name + "_prompt_" + str(self.counter): "",
            self.name + "_models_" + str(self.counter): "Realist - Humanoid",
            self.name + "_negative_" + str(self.counter): "",
            self.name
            + "_predefined_negative_"
            + str(self.counter): "Default humanoid negative",
            self.name + "_status_" + str(self.counter): "Idle",
        }
        # This is a boilerplate function that should be called at the end to make it work with the history
        self.end(tag, history)

        print(tag)
        print(self.settings[tag])

    def pick_image(self, path):
        try:
            image = path
        except Exception:
            print("AN ERROR ON PLUGIN CRUNCHY MOON.")
            return

        image = image.convert("RGBA")
        self.image = image.copy()
        self.image_path = path
        image.thumbnail((450, 450), Image.LANCZOS)
        self.viewer.load(image)
        self.update_output()

    def run(self, tag: str, image: Image = None) -> Image:
        model_id = 0
        file_id = 0
        print(tag)
        current_prompt = self.settings[tag][self.name + "_prompt_" + tag.split("_")[-1]]
        current_model = self.settings[tag][self.name + "_models_" + tag.split("_")[-1]]
        current_negative = self.settings[tag][
            self.name + "_negative_" + tag.split("_")[-1]
        ]
        current_predefined_negative = self.settings[tag][
            self.name + "_predefined_negative_" + tag.split("_")[-1]
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

        processing = self.pick_image(
            Inference().ImagineA(current_prompt, model_id, file_id, current_negative)
        )
        return ""
