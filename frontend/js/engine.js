/**
 * STATIX PRO - Standalone Client-Side Engineering Calculation Engine
 * Enables 100% offline, zero-server standalone execution for Android APK & Desktop
 * Mirrors Beer & Johnston Statics Solvers (Chapters 2 to 10)
 */

const StatixEngine = {

    // --- Linear Algebra Solver: Gaussian Elimination with Partial Pivoting ---
    solveLinearSystem(A, b) {
        const n = b.length;
        // Deep copy matrices
        const M = A.map(row => [...row]);
        const x = [...b];

        for (let i = 0; i < n; i++) {
            // Pivot search
            let maxRow = i;
            for (let k = i + 1; k < n; k++) {
                if (Math.abs(M[k][i]) > Math.abs(M[maxRow][i])) {
                    maxRow = k;
                }
            }
            // Swap rows
            [M[i], M[maxRow]] = [M[maxRow], M[i]];
            [x[i], x[maxRow]] = [x[maxRow], x[i]];

            if (Math.abs(M[i][i]) < 1e-12) {
                throw new Error("ماتریس منفرد است (سازه ناپایدار یا مکانیزم هندسی)");
            }

            // Eliminate
            for (let k = i + 1; k < n; k++) {
                const factor = M[k][i] / M[i][i];
                x[k] -= factor * x[i];
                for (let j = i; j < n; j++) {
                    M[k][j] -= factor * M[i][j];
                }
            }
        }

        // Back substitution
        const res = new Array(n).fill(0);
        for (let i = n - 1; i >= 0; i--) {
            let sum = x[i];
            for (let j = i + 1; j < n; j++) {
                sum -= M[i][j] * res[j];
            }
            res[i] = sum / M[i][i];
        }
        return res;
    },

    // --- 1. BEAM SOLVER ---
    solveBeam(model) {
        const L_total = model.length;
        const nodesSet = new Set([0.0, L_total]);
        model.supports.forEach(s => nodesSet.add(s.x));
        (model.hinges || []).forEach(h => nodesSet.add(h));
        (model.point_loads || []).forEach(p => nodesSet.add(p.x));
        (model.moments || []).forEach(m => nodesSet.add(m.x));
        (model.dist_loads || []).forEach(d => { nodesSet.add(d.x1); nodesSet.add(d.x2); });

        const sortedX = Array.from(nodesSet).sort((a, b) => a - b);
        const hingesSet = new Set((model.hinges || []).map(h => Math.round(h * 1e4) / 1e4));

        let dofCount = 0;
        const nodeDofMap = {};
        sortedX.forEach((x, i) => {
            const vDof = dofCount++;
            const rx = Math.round(x * 1e4) / 1e4;
            if (hingesSet.has(rx)) {
                nodeDofMap[i] = { v: vDof, theta_left: dofCount++, theta_right: dofCount++, x };
            } else {
                nodeDofMap[i] = { v: vDof, theta: dofCount++, x };
            }
        });

        const K = Array.from({ length: dofCount }, () => new Array(dofCount).fill(0));
        const F = new Array(dofCount).fill(0);
        const EI = 2e7; // Nominal rigidity

        for (let i = 0; i < sortedX.length - 1; i++) {
            const x1 = sortedX[i];
            const x2 = sortedX[i + 1];
            const L = x2 - x1;
            if (L <= 1e-7) continue;

            const d1 = nodeDofMap[i];
            const d2 = nodeDofMap[i + 1];
            const v1 = d1.v;
            const t1 = d1.theta_right !== undefined ? d1.theta_right : d1.theta;
            const v2 = d2.v;
            const t2 = d2.theta_left !== undefined ? d2.theta_left : d2.theta;
            const edofs = [v1, t1, v2, t2];

            const kElem = [
                [ 12*EI/(L**3),   6*EI/(L**2), -12*EI/(L**3),   6*EI/(L**2)],
                [  6*EI/(L**2),   4*EI/L,       -6*EI/(L**2),   2*EI/L],
                [-12*EI/(L**3),  -6*EI/(L**2),  12*EI/(L**3),  -6*EI/(L**2)],
                [  6*EI/(L**2),   2*EI/L,       -6*EI/(L**2),   4*EI/L]
            ];

            for (let r = 0; r < 4; r++) {
                for (let c = 0; c < 4; c++) {
                    K[edofs[r]][edofs[c]] += kElem[r][c];
                }
            }

            // Trapezoidal distributed load work on element
            (model.dist_loads || []).forEach(d => {
                const ox1 = Math.max(x1, d.x1);
                const ox2 = Math.min(x2, d.x2);
                if (ox2 > ox1 + 1e-7) {
                    const wa = d.w1 + (d.w2 - d.w1) * ((ox1 - d.x1) / (d.x2 - d.x1) || 0);
                    const wb = d.w1 + (d.w2 - d.w1) * ((ox2 - d.x1) / (d.x2 - d.x1) || 0);
                    const dw = wb - wa;
                    const fe = [
                        wa*L/2 + 3*dw*L/20,
                        wa*L**2/12 + dw*L**2/30,
                        wa*L/2 + 7*dw*L/20,
                        -wa*L**2/12 - dw*L**2/20
                    ];
                    for (let r = 0; r < 4; r++) F[edofs[r]] += fe[r];
                }
            });
        }

        // Point loads & Moments
        (model.point_loads || []).forEach(p => {
            const idx = sortedX.findIndex(x => Math.abs(x - p.x) < 1e-5);
            if (idx !== -1) F[nodeDofMap[idx].v] += p.fy;
        });

        (model.moments || []).forEach(m => {
            const idx = sortedX.findIndex(x => Math.abs(x - m.x) < 1e-5);
            if (idx !== -1) {
                const dofs = nodeDofMap[idx];
                const tdof = dofs.theta !== undefined ? dofs.theta : dofs.theta_right;
                F[tdof] += m.m;
            }
        });

        // Boundary Conditions
        const fixedDofs = {};
        model.supports.forEach(s => {
            const idx = sortedX.findIndex(x => Math.abs(x - s.x) < 1e-5);
            if (idx !== -1) {
                const dofs = nodeDofMap[idx];
                fixedDofs[dofs.v] = 0;
                if (s.type === 'fixed') {
                    if (dofs.theta !== undefined) fixedDofs[dofs.theta] = 0;
                    else { fixedDofs[dofs.theta_left] = 0; fixedDofs[dofs.theta_right] = 0; }
                }
            }
        });

        const freeDofs = [];
        for (let i = 0; i < dofCount; i++) {
            if (!(i in fixedDofs)) freeDofs.push(i);
        }

        if (freeDofs.length === dofCount) throw new Error("تیر هیچ تکیه‌گاهی ندارد (مکانیزم ناپایدار).");

        const Kff = freeDofs.map(r => freeDofs.map(c => K[r][c]));
        const Ff = freeDofs.map(r => F[r]);
        const Uf = this.solveLinearSystem(Kff, Ff);

        const U = new Array(dofCount).fill(0);
        freeDofs.forEach((d, i) => U[d] = Uf[i]);

        // Reactions R = K*U - F
        const R = new Array(dofCount).fill(0);
        for (let i = 0; i < dofCount; i++) {
            let sum = 0;
            for (let j = 0; j < dofCount; j++) sum += K[i][j] * U[j];
            R[i] = sum - F[i];
        }

        const supportReactions = model.supports.map(s => {
            const idx = sortedX.findIndex(x => Math.abs(x - s.x) < 1e-5);
            const dofs = nodeDofMap[idx];
            const Ry = Math.round(R[dofs.v] * 1e4) / 1e4;
            let Rm = 0;
            if (s.type === 'fixed') {
                Rm = Math.round((dofs.theta !== undefined ? R[dofs.theta] : R[dofs.theta_left]) * 1e4) / 1e4;
            }
            return { x: s.x, type: s.type, Ry, Rm, Rx: 0 };
        });

        // Sample points for SFD & BMD
        const numPts = 500;
        const xPts = [];
        for (let i = 0; i <= numPts; i++) xPts.push(i * L_total / numPts);
        sortedX.forEach(cx => {
            if (cx > 1e-5) xPts.push(cx - 1e-5);
            xPts.push(cx);
            if (cx < L_total - 1e-5) xPts.push(cx + 1e-5);
        });
        const augX = Array.from(new Set(xPts)).sort((a, b) => a - b);

        const V_vals = [];
        const M_vals = [];

        augX.forEach(x => {
            let V = 0;
            let M = 0;
            supportReactions.forEach(r => {
                if (r.x <= x) {
                    V += r.Ry;
                    M += r.Ry * (x - r.x) + r.Rm;
                }
            });
            (model.point_loads || []).forEach(p => {
                if (p.x <= x) {
                    V += p.fy;
                    M += p.fy * (x - p.x);
                }
            });
            (model.moments || []).forEach(m => {
                if (m.x <= x) M += m.m;
            });
            (model.dist_loads || []).forEach(d => {
                if (x > d.x1) {
                    const endX = Math.min(x, d.x2);
                    const len = endX - d.x1;
                    if (len > 1e-7) {
                        const span = d.x2 - d.x1;
                        const wEnd = d.w1 + (d.w2 - d.w1) * (len / span);
                        const F_rect = d.w1 * len;
                        const cg_rect = d.x1 + len / 2;
                        V += F_rect;
                        M += F_rect * (x - cg_rect);
                        const F_tri = 0.5 * (wEnd - d.w1) * len;
                        const cg_tri = d.x1 + (2 / 3) * len;
                        V += F_tri;
                        M += F_tri * (x - cg_tri);
                    }
                }
            });
            V_vals.push(Math.round(V * 1e4) / 1e4);
            M_vals.push(Math.round(M * 1e4) / 1e4);
        });

        return {
            success: true,
            length: L_total,
            supports: supportReactions,
            max_shear: Math.max(...V_vals),
            min_shear: Math.min(...V_vals),
            max_moment: Math.max(...M_vals),
            min_moment: Math.min(...M_vals),
            zero_shear_locations: [],
            data_points: {
                x: augX.map(x => Math.round(x * 1e3) / 1e3),
                V: V_vals,
                M: M_vals
            }
        };
    },

    // --- 2. TRUSS SOLVER ---
    solveTruss(model) {
        const nodes = model.nodes;
        const elements = model.elements;
        const numNodes = nodes.length;
        const totalDofs = 2 * numNodes;
        const K = Array.from({ length: totalDofs }, () => new Array(totalDofs).fill(0));
        const F = new Array(totalDofs).fill(0);

        (model.loads || []).forEach(ld => {
            F[2 * ld.node] += (ld.fx || 0);
            F[2 * ld.node + 1] += (ld.fy || 0);
        });

        const fixedDofs = {};
        (model.supports || []).forEach(s => {
            const st = s.type.toLowerCase();
            if (st === 'pin' || st === 'fixed') {
                fixedDofs[2 * s.node] = 0;
                fixedDofs[2 * s.node + 1] = 0;
            } else if (st === 'roller' || st === 'roller_x') {
                fixedDofs[2 * s.node + 1] = 0;
            } else if (st === 'roller_y') {
                fixedDofs[2 * s.node] = 0;
            }
        });

        const elemInfo = elements.map(el => {
            const n1 = nodes[el.node1];
            const n2 = nodes[el.node2];
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const L = Math.hypot(dx, dy);
            const c = dx / L;
            const s = dy / L;
            const E = el.E || 2e11;
            const A = el.A || 0.0025;
            const k = (E * A) / L;

            const ke = [
                [ k*c*c,  k*c*s, -k*c*c, -k*c*s],
                [ k*c*s,  k*s*s, -k*c*s, -k*s*s],
                [-k*c*c, -k*c*s,  k*c*c,  k*c*s],
                [-k*c*s, -k*s*s,  k*c*s,  k*s*s]
            ];
            const dofs = [2*el.node1, 2*el.node1+1, 2*el.node2, 2*el.node2+1];
            for (let r = 0; r < 4; r++) {
                for (let cl = 0; cl < 4; cl++) {
                    K[dofs[r]][dofs[cl]] += ke[r][cl];
                }
            }
            return { L, c, s, E, A, dofs };
        });

        const freeDofs = [];
        for (let i = 0; i < totalDofs; i++) {
            if (!(i in fixedDofs)) freeDofs.push(i);
        }

        const Kff = freeDofs.map(r => freeDofs.map(c => K[r][c]));
        const Ff = freeDofs.map(r => F[r]);
        const Uf = this.solveLinearSystem(Kff, Ff);

        const U = new Array(totalDofs).fill(0);
        freeDofs.forEach((d, i) => U[d] = Uf[i]);

        const memberResults = elemInfo.map((info, idx) => {
            const u = info.dofs.map(d => U[d]);
            const dL = (u[2] - u[0]) * info.c + (u[3] - u[1]) * info.s;
            const force = (info.E * info.A / info.L) * dL;
            const stress = force / info.A;
            const isZero = Math.abs(force) < 1e-2;
            return {
                element_id: idx,
                node1: elements[idx].node1,
                node2: elements[idx].node2,
                length: Math.round(info.L * 1e3) / 1e3,
                force: Math.round(force * 10) / 10,
                abs_force: Math.round(Math.abs(force) * 10) / 10,
                stress_MPa: Math.round((stress / 1e6) * 1e2) / 1e2,
                state: isZero ? 'Zero-Force' : (force > 0 ? 'Tension' : 'Compression'),
                type: isZero ? 'ZERO' : (force > 0 ? 'T' : 'C')
            };
        });

        return {
            success: true,
            determinacy: 'determinate',
            num_nodes: numNodes,
            num_elements: elements.length,
            members: memberResults
        };
    },

    // --- 3. VECTORS & RIGID BODY ---
    solveVectorsDotCross(v1, v2) {
        const dot = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
        const mag1 = Math.hypot(v1.x, v1.y, v1.z);
        const mag2 = Math.hypot(v2.x, v2.y, v2.z);
        const cosTheta = Math.max(-1, Math.min(1, dot / (mag1 * mag2)));
        const angleDeg = (Math.acos(cosTheta) * 180) / Math.PI;

        const cross = {
            x: v1.y * v2.z - v1.z * v2.y,
            y: v1.z * v2.x - v1.x * v2.z,
            z: v1.x * v2.y - v1.y * v2.x
        };
        const crossMag = Math.hypot(cross.x, cross.y, cross.z);

        return {
            dot_product: Math.round(dot * 1e4) / 1e4,
            angle_deg: Math.round(angleDeg * 1e2) / 1e2,
            cross_product: {
                x: Math.round(cross.x * 1e4) / 1e4,
                y: Math.round(cross.y * 1e4) / 1e4,
                z: Math.round(cross.z * 1e4) / 1e4,
                magnitude: Math.round(crossMag * 1e4) / 1e4
            },
            projection_a_on_b: Math.round((dot / mag2) * 1e4) / 1e4
        };
    },

    solveRigidMoment(o, a, f) {
        const r = [a[0] - o[0], a[1] - o[1], a[2] - o[2]];
        const mx = r[1] * f[2] - r[2] * f[1];
        const my = r[2] * f[0] - r[0] * f[2];
        const mz = r[0] * f[1] - r[1] * f[0];
        const mag = Math.hypot(mx, my, mz);
        return {
            r_vector: r.map(k => Math.round(k * 1e3) / 1e3),
            moment_vector: {
                Mx: Math.round(mx * 1e3) / 1e3,
                My: Math.round(my * 1e3) / 1e3,
                Mz: Math.round(mz * 1e3) / 1e3,
                magnitude: Math.round(mag * 1e3) / 1e3
            }
        };
    },

    // --- 4. CENTROIDS ---
    solveCentroids(shapes) {
        let totalA = 0;
        let totalQx = 0;
        let totalQy = 0;
        const table = [];

        shapes.forEach((s, idx) => {
            const sign = s.subtract ? -1 : 1;
            let A = 0, cx = 0, cy = 0;

            if (s.type === 'rectangle') {
                A = s.w * s.h;
                cx = s.x + s.w / 2;
                cy = s.y + s.h / 2;
            } else if (s.type === 'circle') {
                A = Math.PI * (s.r ** 2);
                cx = s.xc;
                cy = s.yc;
            }

            const signedA = sign * A;
            const Qx = signedA * cy;
            const Qy = signedA * cx;

            totalA += signedA;
            totalQx += Qx;
            totalQy += Qy;

            table.push({
                part_id: idx + 1,
                type: s.type,
                is_subtracted: s.subtract,
                area: Math.round(signedA * 10) / 10,
                x_bar: Math.round(cx * 10) / 10,
                y_bar: Math.round(cy * 10) / 10,
                Qx: Math.round(Qx * 10) / 10,
                Qy: Math.round(Qy * 10) / 10
            });
        });

        const xBar = Math.round((totalQy / totalA) * 1e3) / 1e3;
        const yBar = Math.round((totalQx / totalA) * 1e3) / 1e3;

        return {
            success: true,
            total_area: Math.round(totalA * 10) / 10,
            x_bar: xBar,
            y_bar: yBar,
            breakdown_table: table
        };
    },

    // --- 5. INERTIA & MOHR'S CIRCLE ---
    solveInertia(shapes) {
        const cRes = this.solveCentroids(shapes);
        const xBar = cRes.x_bar;
        const yBar = cRes.y_bar;

        let Ix_bar = 0, Iy_bar = 0, Ixy_bar = 0;

        shapes.forEach(s => {
            const sign = s.subtract ? -1 : 1;
            if (s.type === 'rectangle') {
                const A = s.w * s.h;
                const cx = s.x + s.w / 2;
                const cy = s.y + s.h / 2;
                const Ixc = (s.w * (s.h ** 3)) / 12;
                const Iyc = (s.h * (s.w ** 3)) / 12;
                const dx = cx - xBar;
                const dy = cy - yBar;

                Ix_bar += sign * (Ixc + A * (dy ** 2));
                Iy_bar += sign * (Iyc + A * (dx ** 2));
                Ixy_bar += sign * (A * dx * dy);
            }
        });

        const Iavg = (Ix_bar + Iy_bar) / 2;
        const R = Math.hypot((Ix_bar - Iy_bar) / 2, Ixy_bar);
        const Imax = Iavg + R;
        const Imin = Iavg - R;
        const thetaP = (Math.atan2(-2 * Ixy_bar, Ix_bar - Iy_bar) * 180 / Math.PI) / 2;

        return {
            success: true,
            centroidal_moments: {
                I_x_bar: Math.round(Ix_bar),
                I_y_bar: Math.round(Iy_bar),
                I_xy_bar: Math.round(Ixy_bar),
                J_c: Math.round(Ix_bar + Iy_bar)
            },
            radii_of_gyration: {
                kx: Math.round(Math.sqrt(Math.abs(Ix_bar / cRes.total_area)) * 10) / 10,
                ky: Math.round(Math.sqrt(Math.abs(Iy_bar / cRes.total_area)) * 10) / 10
            },
            principal_moments: {
                I_max: Math.round(Imax),
                I_min: Math.round(Imin),
                theta_p_deg: Math.round(thetaP * 10) / 10
            },
            mohr_circle: {
                center: Iavg,
                radius: R
            }
        };
    },

    // --- 6. CABLES ---
    solveParabolicCable(span, sag, w) {
        const T0 = (w * (span ** 2)) / (8 * sag);
        const Vy = (w * span) / 2;
        const Tmax = Math.hypot(T0, Vy);
        const ratio = sag / span;
        const length = span * (1 + (8/3)*(ratio**2) - (32/5)*(ratio**4));

        const xPts = [], yPts = [];
        for (let i = 0; i <= 100; i++) {
            const x = i * span / 100;
            xPts.push(x);
            yPts.push((4 * sag / (span ** 2)) * x * (span - x));
        }

        return {
            success: true,
            span, sag,
            min_tension_T0: Math.round(T0 * 10) / 10,
            max_vertical_reaction: Math.round(Vy * 10) / 10,
            max_tension_Tmax: Math.round(Tmax * 10) / 10,
            cable_length: Math.round(length * 100) / 100,
            profile: { x: xPts, y_sag: yPts }
        };
    },

    // --- 7. FRICTION (SLIP VS TIP) ---
    solveFrictionSlipTip(params) {
        const W = params.weight_W;
        const b = params.width_b;
        const h = params.height_h;
        const y = params.force_height_y;
        const theta = (params.incline_theta_deg * Math.PI) / 180;
        const mu = params.mu_s;

        const P_slip = (W * (Math.sin(theta) + mu * Math.cos(theta))) / 1.0;
        const restoring_M = W * Math.cos(theta) * (b / 2) - W * Math.sin(theta) * (h / 2);
        const P_tip = restoring_M / y;

        const isSlip = P_slip < P_tip;
        const P_crit = isSlip ? P_slip : P_tip;
        const mode = isSlip ? "لغزش (Slipping)" : "واژگونی (Tipping)";
        const note = isSlip
            ? `نیروی لغزش (${P_slip.toFixed(1)} N) کمتر از نیروی واژگونی (${P_tip.toFixed(1)} N) است، بنابراین جسم قبل از چپ شدن سر می‌خورد.`
            : `نیروی واژگونی (${P_tip.toFixed(1)} N) کمتر از نیروی لغزش (${P_slip.toFixed(1)} N) است، بنابراین جسم قبل از سر خوردن واژگون می‌شود.`;

        return {
            success: true,
            friction_angle_deg: Math.round(Math.atan(mu) * 180 / Math.PI * 10) / 10,
            P_slip_critical: Math.round(P_slip * 10) / 10,
            P_tip_critical: Math.round(P_tip * 10) / 10,
            governing_mode: mode,
            P_critical: Math.round(P_crit * 10) / 10,
            comparison_note: note
        };
    }
};
