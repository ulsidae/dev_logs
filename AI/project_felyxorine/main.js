import * as THREE from 'three';

import {
    GLTFLoader
} from 'three/addons/loaders/GLTFLoader.js';

import {
    VRMLoaderPlugin
} from '@pixiv/three-vrm';


const scene = new THREE.Scene();

scene.background =
    new THREE.Color(0x202020);


const DEFAULT_CAMERA_X = 0;
const DEFAULT_CAMERA_Y = 1.4;
const DEFAULT_CAMERA_Z = 3;

const camera =
    new THREE.PerspectiveCamera(
        30,
        window.innerWidth / window.innerHeight,
        0.1,
        100
    );

camera.position.set(
    DEFAULT_CAMERA_X,
    DEFAULT_CAMERA_Y,
    DEFAULT_CAMERA_Z
);

const renderer =
    new THREE.WebGLRenderer({
        antialias: true
    });

renderer.setSize(
    window.innerWidth,
    window.innerHeight
);

renderer.setPixelRatio(
    Math.min(
        window.devicePixelRatio,
        2
    )
);

document.body.appendChild(
    renderer.domElement
);



scene.add(
    new THREE.AmbientLight(
        0xffffff,
        2
    )
);

const light =
    new THREE.DirectionalLight(
        0xffffff,
        3
    );

light.position.set(
    1,
    2,
    3
);

scene.add(light);


const loader =
    new GLTFLoader();

loader.register(
    parser =>
        new VRMLoaderPlugin(parser)
);

let vrm = null;



loader.load(

    './avatar.vrm',

    gltf => {

        vrm =
            gltf.userData.vrm;


        if (!vrm) {

            console.error(
                'VRM error; Can\'t find'
            );

            return;

        }


        scene.add(
            vrm.scene
        );


        vrm.scene.rotation.y =
            Math.PI;


        vrm.scene.position.set(
            0,
            0,
            0
        );


        vrm.scene.scale.set(
            1,
            1,
            1
        );


        console.log(
            'VRM loaded:',
            vrm
        );


        console.log(
            'Humanoid:',
            vrm.humanoid
        );

        const humanoid =
            vrm.humanoid;


        const names = [

            'leftUpperArm',
            'leftLowerArm',
            'leftHand',

            'rightUpperArm',
            'rightLowerArm',
            'rightHand'

        ];


        for (
            const name of names
        ) {

            const bone =
                humanoid.getNormalizedBoneNode(
                    name
                );


            console.log(
                name,
                bone
                    ? bone.name
                    : 'NOT FOUND'
            );

        }

        setArmsDown();

    },

    undefined,

    error => {

        console.error(
            'VRM LOAD ERROR:',
            error
        );

    }

);


function rotateBone(
    bone,
    x,
    y,
    z
) {

    if (!bone) {
        return;
    }


    const q =
        new THREE.Quaternion();


    q.setFromEuler(

        new THREE.Euler(
            x,
            y,
            z,
            'XYZ'
        )

    );


    bone.quaternion.copy(q);

}


function setArmsDown() {

    if (!vrm) {
        return;
    }


    const humanoid =
        vrm.humanoid;


    const leftUpperArm =
        humanoid.getNormalizedBoneNode(
            'leftUpperArm'
        );


    const rightUpperArm =
        humanoid.getNormalizedBoneNode(
            'rightUpperArm'
        );


    const leftLowerArm =
        humanoid.getNormalizedBoneNode(
            'leftLowerArm'
        );


    const rightLowerArm =
        humanoid.getNormalizedBoneNode(
            'rightLowerArm'
        );


    const leftHand =
        humanoid.getNormalizedBoneNode(
            'leftHand'
        );


    const rightHand =
        humanoid.getNormalizedBoneNode(
            'rightHand'
        );


    console.log(
        'ARM BONES',
        {
            leftUpperArm,
            rightUpperArm,
            leftLowerArm,
            rightLowerArm
        }
    );

    rotateBone(
        leftUpperArm,
        0,
        0,
        89
    );


    rotateBone(
        rightUpperArm,
        0,
        0,
        -89
    );

    rotateBone(
        leftLowerArm,
        0,
        0,
        -0.08
    );


    rotateBone(
        rightLowerArm,
        0,
        0,
        0.08
    );


    rotateBone(
        leftHand,
        0,
        0,
        0
    );


    rotateBone(
        rightHand,
        0,
        0,
        0
    );


}

const zoomSlider =
    document.getElementById(
        'zoom-slider'
    );


const xSlider =
    document.getElementById(
        'x-slider'
    );


const ySlider =
    document.getElementById(
        'y-slider'
    );


const scaleSlider =
    document.getElementById(
        'scale-slider'
    );


const resetCamera =
    document.getElementById(
        'reset-camera'
    );


if (zoomSlider) {

    zoomSlider.addEventListener(
        'input',
        () => {

            camera.position.z =
                Number(
                    zoomSlider.value
                );

        }
    );

}


if (xSlider) {

    xSlider.addEventListener(
        'input',
        () => {

            camera.position.x =
                Number(
                    xSlider.value
                );

        }
    );

}


if (ySlider) {

    ySlider.addEventListener(
        'input',
        () => {

            camera.position.y =

                DEFAULT_CAMERA_Y +

                Number(
                    ySlider.value
                );

        }
    );

}


if (scaleSlider) {

    scaleSlider.addEventListener(
        'input',
        () => {

            if (!vrm) {
                return;
            }


            const scale =
                Number(
                    scaleSlider.value
                );


            vrm.scene.scale.set(
                scale,
                scale,
                scale
            );

        }
    );

}


if (resetCamera) {

    resetCamera.addEventListener(
        'click',
        () => {

            camera.position.set(
                DEFAULT_CAMERA_X,
                DEFAULT_CAMERA_Y,
                DEFAULT_CAMERA_Z
            );


            if (vrm) {

                vrm.scene.position.set(
                    0,
                    0,
                    0
                );


                vrm.scene.scale.set(
                    1,
                    1,
                    1
                );


                setArmsDown();

            }


            if (zoomSlider) {

                zoomSlider.value =
                    DEFAULT_CAMERA_Z;

            }


            if (xSlider) {

                xSlider.value =
                    DEFAULT_CAMERA_X;

            }


            if (ySlider) {

                ySlider.value =
                    0;

            }


            if (scaleSlider) {

                scaleSlider.value =
                    1;

            }

        }
    );

}


window.addEventListener(

    'wheel',

    event => {

        camera.position.z +=
            event.deltaY * 0.002;


        camera.position.z =
            THREE.MathUtils.clamp(
                camera.position.z,
                1.5,
                6
            );


        if (zoomSlider) {

            zoomSlider.value =
                camera.position.z;

        }

    },

    {
        passive: true
    }

);


let blinkTimer = 0;

let blinking = false;

let blinkDuration = 0;


const BLINK_INTERVAL = 0.9;

const BLINK_DURATION = 0.14;

let isTalking = false;

let talkTimer = 0;


function updateBlink(delta) {

    if (
        !vrm ||
        !vrm.expressionManager
    ) {
        return;
    }


    blinkTimer += delta;


    if (
        !blinking &&
        blinkTimer >= BLINK_INTERVAL
    ) {

        blinking = true;

        blinkDuration = 0;

    }


    if (!blinking) {
        return;
    }


    blinkDuration += delta;


    const progress =
        blinkDuration /
        BLINK_DURATION;


    let value;


    if (progress < 0.5) {

        value =
            progress * 2;

    }

    else {

        value =
            2 -
            progress * 2;

    }


    value =
        THREE.MathUtils.clamp(
            value,
            0,
            1
        );


    vrm.expressionManager.setValue(
        'blink',
        value
    );


    if (
        blinkDuration >=
        BLINK_DURATION
    ) {

        vrm.expressionManager.setValue(
            'blink',
            0
        );


        blinking = false;

        blinkTimer = 0;

    }

}


function updateTalking(delta) {

    if (
        !vrm ||
        !vrm.expressionManager
    ) {
        return;
    }


    if (!isTalking) {

        vrm.expressionManager.setValue(
            'aa',
            0
        );

        return;

    }



    talkTimer += delta;

    const mouth =
        (
            Math.sin(
                talkTimer * 18
            ) + 1
        ) * 0.5;


    vrm.expressionManager.setValue(
        'aa',
        mouth * 0.8
    );

}


function startTalking() {

    isTalking = true;

    talkTimer = 0;

}


function stopTalking() {

    isTalking = false;

    talkTimer = 0;


    if (
        vrm &&
        vrm.expressionManager
    ) {

        vrm.expressionManager.setValue(
            'aa',
            0
        );

    }

}

const clock =
    new THREE.Clock();


    function animate() {

        requestAnimationFrame(
            animate
        );


        const delta =
            clock.getDelta();


        if (vrm) {

            vrm.update(
                delta
            );

        }


        updateBlink(
            delta
        );


        updateTalking(
            delta
        );


        renderer.render(
            scene,
            camera
        );

    }


animate();


window.addEventListener(
    'resize',
    () => {

        camera.aspect =
            window.innerWidth /
            window.innerHeight;


        camera.updateProjectionMatrix();


        renderer.setSize(
            window.innerWidth,
            window.innerHeight
        );

    }
);


const chat =
    document.getElementById(
        'chat'
    );

const chatHeader =
    document.getElementById(
        'chat-header'
    );

const chatHide =
    document.getElementById(
        'chat-hide'
    );

const showChat =
    document.getElementById(
        'show-chat'
    );

const chatResize =
    document.getElementById(
        'chat-resize'
    );


const controls =
    document.getElementById(
        'controls'
    );

const controlsHeader =
    document.getElementById(
        'controls-header'
    );

const controlsHide =
    document.getElementById(
        'controls-hide'
    );

const showControls =
    document.getElementById(
        'show-controls'
    );

chatHide.addEventListener(
    'click',
    () => {

        chat.style.display =
            'none';

        showChat.style.display =
            'block';

    }
);


showChat.addEventListener(
    'click',
    () => {

        chat.style.display =
            'flex';

        showChat.style.display =
            'none';

    }
);

controlsHide.addEventListener(
    'click',
    () => {

        controls.style.display =
            'none';

        showControls.style.display =
            'block';

    }
);


showControls.addEventListener(
    'click',
    () => {

        controls.style.display =
            'flex';

        showControls.style.display =
            'none';

    }
);

function makeDraggable(
    element,
    handle
) {

    let dragging = false;

    let startX = 0;
    let startY = 0;

    let startLeft = 0;
    let startTop = 0;


    handle.addEventListener(
        'pointerdown',
        event => {


            if (
                event.target.tagName ===
                'BUTTON'
            ) {

                return;

            }


            dragging = true;


            const rect =
                element.getBoundingClientRect();


            startX =
                event.clientX;

            startY =
                event.clientY;


            startLeft =
                rect.left;

            startTop =
                rect.top;


            element.style.left =
                `${startLeft}px`;

            element.style.top =
                `${startTop}px`;

            element.style.right =
                'auto';

            element.style.bottom =
                'auto';


            handle.setPointerCapture(
                event.pointerId
            );

        }
    );


    handle.addEventListener(
        'pointermove',
        event => {

            if (!dragging) {
                return;
            }


            const dx =
                event.clientX -
                startX;

            const dy =
                event.clientY -
                startY;


            let left =
                startLeft + dx;

            let top =
                startTop + dy;

            const maxLeft =
                window.innerWidth -
                element.offsetWidth;

            const maxTop =
                window.innerHeight -
                element.offsetHeight;


            left =
                Math.max(
                    0,
                    Math.min(
                        left,
                        maxLeft
                    )
                );


            top =
                Math.max(
                    0,
                    Math.min(
                        top,
                        maxTop
                    )
                );


            element.style.left =
                `${left}px`;

            element.style.top =
                `${top}px`;

        }
    );


    handle.addEventListener(
        'pointerup',
        event => {

            dragging = false;


            try {

                handle.releasePointerCapture(
                    event.pointerId
                );

            } catch {

            }

        }
    );

}


makeDraggable(
    chat,
    chatHeader
);


makeDraggable(
    controls,
    controlsHeader
);

let resizing = false;

let resizeStartX = 0;
let resizeStartY = 0;

let resizeStartWidth = 0;
let resizeStartHeight = 0;


chatResize.addEventListener(
    'pointerdown',
    event => {

        resizing = true;


        resizeStartX =
            event.clientX;

        resizeStartY =
            event.clientY;


        resizeStartWidth =
            chat.offsetWidth;

        resizeStartHeight =
            chat.offsetHeight;


        chatResize.setPointerCapture(
            event.pointerId
        );

    }
);


chatResize.addEventListener(
    'pointermove',
    event => {

        if (!resizing) {
            return;
        }


        const dx =
            event.clientX -
            resizeStartX;

        const dy =
            event.clientY -
            resizeStartY;


        const width =
            Math.max(
                280,
                resizeStartWidth + dx
            );


        const height =
            Math.max(
                220,
                resizeStartHeight + dy
            );


        chat.style.width =
            `${width}px`;

        chat.style.height =
            `${height}px`;

    }
);


chatResize.addEventListener(
    'pointerup',
    event => {

        resizing = false;


        try {

            chatResize.releasePointerCapture(
                event.pointerId
            );

        } catch {


        }

    }
);

/* It didn't work. But, code still works. I guess(?)*/
function detectEmotion(text) {

    const lower =
        text.toLowerCase();


    if (
        /lol|haha|happy|great|awesome/
            .test(lower)
    ) {

        return 'happy';

    }


    if (
        /sad|depress|lonely|cry/
            .test(lower)
    ) {

        return 'sad';

    }


    if (
        /angry|mad|annoy/
            .test(lower)
    ) {

        return 'angry';

    }


    if (
        /wow|really|surprise/
            .test(lower)
    ) {

        return 'surprised';

    }


    return 'neutral';

}
/*^ calibrate these.*/

const messages =
    document.getElementById('messages');

const input =
    document.getElementById('message-input');

const sendButton =
    document.getElementById('send-button');


const conversation = [ ];


function addMessage(
    text,
    type
) {

    const message =
        document.createElement('div');

    message.className =
        `message ${type}`;

    message.textContent =
        text;

    messages.appendChild(
        message
    );

    messages.scrollTop =
        messages.scrollHeight;

    return message;

}

async function sendMessage() {

    const text =
        input.value.trim();


    if (!text) {
        return;
    }

    addMessage(
        text,
        'user'
    );


    input.value = '';

    input.disabled = true;

    sendButton.disabled = true;

    conversation.push({

        role: 'user',

        content: text

    });

    const thinking =
        addMessage(
            'thinking...',
            'assistant'
        );


    try {

        const response =
            await fetch(
                '/api/chat',
                {

                    method: 'POST',

                    headers: {
                        'Content-Type':
                            'application/json'
                    },

                    body: JSON.stringify({

                        messages:
                            conversation

                    })

                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        if (data.error) {

            throw new Error(
                data.error
            );

        }


        const reply =
            data.reply ||
            'no response.';

        thinking.textContent =
            reply;

        conversation.push({

            role: 'assistant',

            content: reply

        });

        const emotion =
            detectEmotion(reply);


        console.log(
            'Emotion:',
            emotion
        );


        startTalking();

        const talkingTime =
            Math.max(
                1000,
                Math.min(
                    7000,
                    reply.length * 80
                )
            );


        setTimeout(
            () => {

                stopTalking();

            },
            talkingTime
        );


    } catch (error) {

        console.error(
            'Ollama error:',
            error
        );


        thinking.textContent =
            `Ollama failed: ${error.message}`;

    }


    input.disabled = false;

    sendButton.disabled = false;

    input.focus();

}


sendButton.addEventListener(
    'click',
    sendMessage
);


input.addEventListener(
    'keydown',
    event => {

        if (
            event.key === 'Enter'
        ) {

            event.preventDefault();

            sendMessage();

        }

    }
);
