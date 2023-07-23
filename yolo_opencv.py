import cv2
import numpy as np
import time
import config
import asyncio
import aiohttp

from tv_operations import toggleTvStatus

config_file = config.config_file
weights_file = config.weights_file
classes_file = config.classes_file

def get_output_layers(net):
    layer_names = net.getLayerNames()
    try:
        output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    except:
        output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    return output_layers

def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    label = str(classes[class_id])
    confidence_percent = "{:.2f}%".format(confidence * 100)
    label_with_conf = f"{label} {confidence_percent}"
    color = COLORS[class_id]
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
    cv2.putText(img, label_with_conf, (x-10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

async def call_tv_on_api(tv_curr_status):
    try:
        async with aiohttp.ClientSession() as session:
            tv_status = await toggleTvStatus(session, status=True)
        if tv_status is not None:
            print("TV On API called Success")
            return True  # Return the TV status from the API call
        else:
            print("TV On API request failed or TV not found.")
            return tv_curr_status
    except aiohttp.ClientError as e:
        print(f"TV On API request error: {e}")
    return tv_curr_status
    

async def call_tv_off_api(tv_curr_status):
    try:
        async with aiohttp.ClientSession() as session:
            tv_status = await toggleTvStatus(session, status=False)
        if tv_status is not None:
            print("TV Off API called Success")
            return False  # Return the TV status from the API call
        else:
            print("TV Off API request failed or TV not found.")
            return tv_curr_status
    except aiohttp.ClientError as e:
        print(f"TV Off API request error: {e}")
    return tv_curr_status

# Load YOLO model
net = cv2.dnn.readNet(weights_file, config_file)

# Load class names
classes = None
with open(classes_file, 'r') as f:
    classes = [line.strip() for line in f.readlines()]

# Find the class ID for "person"
person_class_id = classes.index("person")

# Random colors for bounding boxes
COLORS = np.random.uniform(0, 255, size=(len(classes), 3))

async def main():
    # Initialize webcam
    video_capture = cv2.VideoCapture(0)  # 0 represents the default camera (usually the built-in laptop camera)

    # Reduce the input size for faster processing
    net_width = 320
    net_height = 320

    # Variables for time tracking
    person_detected_time = None
    person_not_detected_time = None
    tv_on = False

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        Height, Width = frame.shape[:2]
        scale = 1.0 / 255.0

        blob = cv2.dnn.blobFromImage(frame, scale, (net_width, net_height), (0, 0, 0), swapRB=True, crop=False)

        net.setInput(blob)

        outs = net.forward(get_output_layers(net))

        class_ids = []
        confidences = []
        boxes = []
        conf_threshold = 0.5
        nms_threshold = 0.4

        person_detected = False

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > conf_threshold:
                    center_x = int(detection[0] * Width)
                    center_y = int(detection[1] * Height)
                    w = int(detection[2] * Width)
                    h = int(detection[3] * Height)
                    x = center_x - w / 2
                    y = center_y - h / 2
                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])

                    if class_id == person_class_id:
                        person_detected = True

        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

        for i in indices:
            try:
                box = boxes[i]
            except:
                i = i[0]
                box = boxes[i]

            x, y, w, h = box
            draw_prediction(frame, class_ids[i], confidences[i], round(x), round(y), round(x + w), round(y + h))

        if person_detected:
            if person_detected_time is None:
                person_detected_time = time.time()
                print("Person detected:", "detectTime: ", person_detected_time, "TV Status: ", tv_on)
            person_not_detected_time = None
            if time.time() - person_detected_time >= 5 and not tv_on:
                print("TV On at:" , person_detected_time)
                # tv_on = await call_tv_on_api(tv_on)
                cv2.putText(frame, "TV On", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                tv_on = True
        else:
            if person_not_detected_time is None:
                person_not_detected_time = time.time()
                print("Person not detected:", "detectTime: ", person_detected_time, "TV Status: ", tv_on)
            person_detected_time = None
            if time.time() - person_not_detected_time >= 5 and tv_on:
                print("TV Off at:" , person_not_detected_time)
                # tv_on = await call_tv_off_api(tv_on)
                cv2.putText(frame, "TV Off", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                tv_on = False

        cv2.imshow("object detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(main())
