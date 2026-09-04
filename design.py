import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Streamlit 3D 탱크 시뮬레이션", layout="wide")

st.title("🚜 3D 탱크 시뮬레이터")
st.caption("Streamlit + Three.js를 활용한 실시간 3D 탱크 조종 및 포격")

# 조작 키 안내
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **[엔진 조작]**
    * **J**: 엔진 시작
    * **H**: 엔진 정지
    """)
with col2:
    st.markdown("""
    **[탱크 조종 & 포격]** (엔진 ON 상태)
    * **W**: 전진 | **S**: 후진
    * **A**: 좌회전 | **D**: 우회전
    * **F**: 포탄 발사 🔥
    """)

# 3D 캔버스 및 Three.js 게임 로직 HTML/JS
html_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background-color: #1a1a1a; font-family: sans-serif; }
        #canvas-container { width: 100vw; height: 100vh; position: relative; }
        #hud {
            position: absolute;
            top: 20px;
            left: 20px;
            color: #00ff00;
            font-size: 20px;
            font-weight: bold;
            background: rgba(0, 0, 0, 0.7);
            padding: 10px 20px;
            border-radius: 8px;
            border: 1px solid #00ff00;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="canvas-container">
        <div id="hud">엔진 상태: OFF (J를 눌러 시작)</div>
    </div>

    <script>
        // 기본 3D 씬 설정
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1a1a1a);

        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // 조명
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(20, 40, 20);
        dirLight.castShadow = true;
        scene.add(dirLight);

        // 바닥 (지형)
        const gridHelper = new THREE.GridHelper(200, 50, 0x00ff00, 0x444444);
        gridHelper.position.y = -0.01;
        scene.add(gridHelper);

        const planeGeo = new THREE.PlaneGeometry(200, 200);
        const planeMat = new THREE.MeshStandardMaterial({ color: 0x222222 });
        const plane = new THREE.Mesh(planeGeo, planeMat);
        plane.rotation.x = -Math.PI / 2;
        plane.receiveShadow = true;
        scene.add(plane);

        // 탱크 개체 생성 (Group)
        const tank = new THREE.Group();

        // 탱크 차체 (Body)
        const bodyGeo = new THREE.BoxGeometry(3, 1.2, 4);
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x2e5a27 });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.y = 0.8;
        body.castShadow = true;
        tank.add(body);

        // 포탑 (Turret)
        const turretGeo = new THREE.BoxGeometry(2, 0.8, 2);
        const turretMat = new THREE.MeshStandardMaterial({ color: 0x3d7534 });
        const turret = new THREE.Mesh(turretGeo, turretMat);
        turret.position.set(0, 1.8, -0.2);
        turret.castShadow = true;
        tank.add(turret);

        // 포신 (Cannon)
        const cannonGeo = new THREE.CylinderGeometry(0.15, 0.15, 2.5, 16);
        const cannonMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
        const cannon = new THREE.Mesh(cannonGeo, cannonMat);
        cannon.rotation.x = Math.PI / 2;
        cannon.position.set(0, 1.8, 1.5);
        cannon.castShadow = true;
        tank.add(cannon);

        scene.add(tank);

        // 포탄 배열 및 재사용 가능한 리소스
        const bullets = [];
        const bulletGeo = new THREE.SphereGeometry(0.25, 8, 8);
        const bulletMat = new THREE.MeshStandardMaterial({ color: 0xffa500, emissive: 0xff3300 });

        // 상태 변수
        let isEngineOn = false;
        const keys = {};
        const speed = 0.15;
        const turnSpeed = 0.03;
        const bulletSpeed = 1.2;

        // HUD 업데이트
        const hud = document.getElementById('hud');

        function updateHUD() {
            if (isEngineOn) {
                hud.innerText = "엔진 상태: ON (WASD 조종 / F 발사)";
                hud.style.color = "#00ff00";
                hud.style.borderColor = "#00ff00";
            } else {
                hud.innerText = "엔진 상태: OFF (J를 눌러 시작)";
                hud.style.color = "#ff3333";
                hud.style.borderColor = "#ff3333";
            }
        }

        // 포탄 발사 함수
        function fireBullet() {
            if (!isEngineOn) return;

            const bullet = new THREE.Mesh(bulletGeo, bulletMat);
            
            // 포신 끝 위치 계산
            const muzzleOffset = new THREE.Vector3(0, 1.8, 2.8);
            muzzleOffset.applyMatrix4(tank.matrixWorld);
            bullet.position.copy(muzzleOffset);

            // 탱크가 바라보는 전방 방향 벡터 추출
            const direction = new THREE.Vector3(0, 0, 1);
            direction.applyQuaternion(tank.quaternion).normalize();

            bullets.push({
                mesh: bullet,
                direction: direction,
                life: 120 // 프레임 기준 생명주기 (약 2초)
            });

            scene.add(bullet);
        }

        // 키보드 이벤트
        window.addEventListener('keydown', (e) => {
            const key = e.key.toLowerCase();
            keys[key] = true;

            // 엔진 시작/정지
            if (key === 'j') {
                isEngineOn = true;
                updateHUD();
            } else if (key === 'h') {
                isEngineOn = false;
                updateHUD();
            } else if (key === 'f') {
                fireBullet();
            }
        });

        window.addEventListener('keyup', (e) => {
            keys[e.key.toLowerCase()] = false;
        });

        // 애니메이션 루프
        function animate() {
            requestAnimationFrame(animate);

            if (isEngineOn) {
                // W: 전진
                if (keys['w']) {
                    tank.translateZ(speed);
                }
                // S: 후진
                if (keys['s']) {
                    tank.translateZ(-speed);
                }
                // A: 좌회전
                if (keys['a']) {
                    tank.rotation.y += turnSpeed;
                }
                // D: 우회전
                if (keys['d']) {
                    tank.rotation.y -= turnSpeed;
                }
            }

            // 포탄 이동 및 수명 관리
            for (let i = bullets.length - 1; i >= 0; i--) {
                const b = bullets[i];
                b.mesh.position.addScaledVector(b.direction, bulletSpeed);
                b.life -= 1;

                // 수명이 다했거나 바닥 아래로 내려가면 제거
                if (b.life <= 0) {
                    scene.remove(b.mesh);
                    b.mesh.geometry.dispose();
                    bullets.splice(i, 1);
                }
            }

            // 카메라는 항상 탱크 뒤쪽 위에서 추적
            const relativeCameraOffset = new THREE.Vector3(0, 6, -12);
            const cameraOffset = relativeCameraOffset.applyMatrix4(tank.matrixWorld);
            camera.position.x = cameraOffset.x;
            camera.position.y = cameraOffset.y;
            camera.position.z = cameraOffset.z;
            camera.lookAt(tank.position.x, tank.position.y + 1, tank.position.z);

            renderer.render(scene, camera);
        }

        // 윈도우 리사이즈 대응
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        animate();
    </script>
</body>
</html>
"""

# Streamlit 내에 3D Render 컴포넌트 렌더링
components.html(html_code, height=650)
