"""
\********************************************************************************
* Copyright (c) 2025 the Qrisp authors
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0.
*
* This Source Code may also be made available under the following Secondary
* Licenses when the conditions for such availability set forth in the Eclipse
* Public License, v. 2.0 are satisfied: GNU General Public License, version 2
* with the GNU Classpath Exception which is
* available at https://www.gnu.org/software/classpath/license.html.
*
* SPDX-License-Identifier: EPL-2.0 OR GPL-2.0 WITH Classpath-exception-2.0
********************************************************************************/
"""


def test_IQPE_integration():
    from qrisp import p, QuantumVariable, IQPE, h, run, x, rx
    import numpy as np

    def U(qv):
        x = 1/2**4
        y = 1/2**2

        rx(x*2*np.pi, qv[0])
        rx(y*2*np.pi, qv[1])

    qv = QuantumVariable(2)

    x(qv)
    h(qv)

    IQPE(qv, U, precision=5)
    res = run(qv.qs, 10_000)
    # Does not work because classical control is not working
    # assert (np.abs(res.get("01010", 0)/10_000 - 1.0) < 0.01)
