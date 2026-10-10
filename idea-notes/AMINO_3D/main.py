import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


AMINO_ACIDS = {
    "Nonpolar": [
        ("Glycine", "Gly", "[NH3+]CC(=O)[O-]"),
        ("Alanine", "Ala", "C[C@@H]([NH3+])C(=O)[O-]"),
        ("Valine", "Val", "CC(C)[C@@H]([NH3+])C(=O)[O-]"),
        ("Leucine", "Leu", "CC(C)C[C@@H]([NH3+])C(=O)[O-]"),
        ("Isoleucine", "Ile", "CC[C@H](C)[C@@H]([NH3+])C(=O)[O-]"),
        ("Methionine", "Met", "CSCC[C@@H]([NH3+])C(=O)[O-]"),
        ("Phenylalanine", "Phe", "[NH3+][C@@H](Cc1ccccc1)C(=O)[O-]"),
        ("Tryptophan", "Trp", "[NH3+][C@@H](Cc1c[nH]c2ccccc12)C(=O)[O-]"),
        ("Proline", "Pro", "O=C([O-])[C@@H]1CCC[NH2+]1"),
    ],
    "Polar": [
        ("Serine", "Ser", "[NH3+][C@@H](CO)C(=O)[O-]"),
        ("Threonine", "Thr", "C[C@H](O)[C@@H]([NH3+])C(=O)[O-]"),
        ("Cysteine", "Cys", "[NH3+][C@@H](CS)C(=O)[O-]"),
        ("Tyrosine", "Tyr", "[NH3+][C@@H](Cc1ccc(O)cc1)C(=O)[O-]"),
        ("Asparagine", "Asn", "[NH3+][C@@H](CC(N)=O)C(=O)[O-]"),
        ("Glutamine", "Gln", "[NH3+][C@@H](CCC(N)=O)C(=O)[O-]"),
    ],
    "Electrically Charged": [
        ("Aspartic acid", "Asp", "[NH3+][C@@H](CC(=O)[O-])C(=O)[O-]"),
        ("Glutamic acid", "Glu", "[NH3+][C@@H](CCC(=O)[O-])C(=O)[O-]"),
        ("Lysine", "Lys", "[NH3+][C@@H](CCCC[NH3+])C(=O)[O-]"),
        ("Arginine", "Arg", "[NH3+][C@@H](CCCNC(N)=[NH2+])C(=O)[O-]"),
        ("Histidine", "His", "[NH3+][C@@H](Cc1cnc[nH]1)C(=O)[O-]"),
    ],
}

ATOM_COLORS = {
    "C": "#65758B",
    "N": "#4389F5",
    "O": "#F05260",
    "S": "#E8BF42",
    "P": "#E89145",
    "H": "#E6EBF2",
    "F": "#63C174",
    "Cl": "#63C174",
    "Br": "#A66BD4",
    "I": "#9B78D1",
}

ATOM_SIZES = {
    "C": 150,
    "N": 200,
    "O": 200,
    "S": 240,
    "P": 230,
    "H": 45,
    "F": 150,
    "Cl": 180,
    "Br": 210,
    "I": 230,
}


class AminoAcidViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("AMINO / 3D")
        self.root.geometry("1120x780")
        self.root.minsize(900, 620)
        self.root.configure(bg="#10141D")

        self.category = tk.StringVar(value="Nonpolar")
        self.selected = tk.StringVar()
        self.show_hydrogens = tk.BooleanVar(value=True)
        self.show_labels = tk.BooleanVar(value=True)

        self.mol = None
        self.coords = None
        self.view_elev = 22
        self.view_azim = 35
        self.zoom = 1.0
        self.dragging = False
        self.last_mouse = None
        self.home_limits = None

        self.build_ui()
        self.update_amino_acids()

    def build_ui(self):
        sidebar = tk.Frame(self.root, bg="#171D29", width=270)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="AMINO / 3D",
            bg="#171D29",
            fg="#72E0CB",
            font=("Consolas", 23, "bold"),
        ).pack(anchor="w", padx=22, pady=(25, 4))

        tk.Label(
            sidebar,
            text="MOLECULAR EXPLORER",
            bg="#171D29",
            fg="#8391A7",
            font=("Consolas", 9),
        ).pack(anchor="w", padx=24, pady=(0, 28))

        tk.Label(
            sidebar,
            text="CLASSIFICATION",
            bg="#171D29",
            fg="#AEBACB",
            font=("Consolas", 10, "bold"),
        ).pack(anchor="w", padx=20, pady=(0, 8))

        self.category_box = ttk.Combobox(
            sidebar,
            textvariable=self.category,
            values=list(AMINO_ACIDS),
            state="readonly",
            font=("Consolas", 10),
        )
        self.category_box.pack(fill="x", padx=18, pady=(0, 20))
        self.category_box.bind(
            "<<ComboboxSelected>>",
            self.update_amino_acids,
        )

        tk.Label(
            sidebar,
            text="AMINO ACIDS",
            bg="#171D29",
            fg="#AEBACB",
            font=("Consolas", 10, "bold"),
        ).pack(anchor="w", padx=20, pady=(0, 8))

        self.amino_box = ttk.Combobox(
            sidebar,
            textvariable=self.selected,
            state="readonly",
            font=("Consolas", 11),
        )
        self.amino_box.pack(fill="x", padx=18)
        self.amino_box.bind(
            "<<ComboboxSelected>>",
            self.select_amino,
        )

        self.count_label = tk.Label(
            sidebar,
            text="",
            bg="#171D29",
            fg="#72E0CB",
            font=("Consolas", 10),
        )
        self.count_label.pack(anchor="w", padx=20, pady=(10, 25))

        tk.Label(
            sidebar,
            text="DISPLAY",
            bg="#171D29",
            fg="#AEBACB",
            font=("Consolas", 10, "bold"),
        ).pack(anchor="w", padx=20, pady=(0, 8))

        tk.Checkbutton(
            sidebar,
            text="Hydrogen atoms",
            variable=self.show_hydrogens,
            command=self.draw_molecule,
            bg="#171D29",
            fg="#D7DFEA",
            selectcolor="#252E3D",
            activebackground="#171D29",
            activeforeground="#72E0CB",
            font=("Consolas", 10),
        ).pack(anchor="w", padx=18)

        tk.Checkbutton(
            sidebar,
            text="Atom labels",
            variable=self.show_labels,
            command=self.draw_molecule,
            bg="#171D29",
            fg="#D7DFEA",
            selectcolor="#252E3D",
            activebackground="#171D29",
            activeforeground="#72E0CB",
            font=("Consolas", 10),
        ).pack(anchor="w", padx=18, pady=(2, 18))

        tk.Label(
            sidebar,
            text="ATOM COLORS",
            bg="#171D29",
            fg="#AEBACB",
            font=("Consolas", 10, "bold"),
        ).pack(anchor="w", padx=20, pady=(0, 10))

        for element in ("C", "N", "O", "S", "P", "H"):
            row = tk.Frame(sidebar, bg="#171D29")
            row.pack(anchor="w", padx=23, pady=2)

            tk.Label(
                row,
                text="●",
                fg=ATOM_COLORS[element],
                bg="#171D29",
                font=("Arial", 12),
            ).pack(side="left")

            tk.Label(
                row,
                text=f"  {element}",
                fg="#D7DFEA",
                bg="#171D29",
                font=("Consolas", 10),
            ).pack(side="left")

        tk.Label(
            sidebar,
            text="20 STANDARD AMINO ACIDS",
            bg="#171D29",
            fg="#65748B",
            font=("Consolas", 8),
        ).pack(side="bottom", anchor="w", padx=20, pady=20)

        main = tk.Frame(self.root, bg="#10141D")
        main.pack(side="left", fill="both", expand=True)

        self.name_label = tk.Label(
            main,
            text="Select an amino acid",
            bg="#10141D",
            fg="#F1F4F9",
            font=("Segoe UI", 23, "bold"),
        )
        self.name_label.pack(anchor="w", padx=28, pady=(23, 2))

        self.info_label = tk.Label(
            main,
            text="",
            bg="#10141D",
            fg="#72E0CB",
            font=("Consolas", 10),
        )
        self.info_label.pack(anchor="w", padx=30, pady=(0, 8))

        self.figure = Figure(
            figsize=(8, 6),
            dpi=100,
            facecolor="#10141D",
        )
        self.ax = self.figure.add_subplot(111, projection="3d")
        self.ax.set_facecolor("#10141D")

        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=main,
        )
        self.canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=12,
        )

        self.canvas.mpl_connect(
            "button_press_event",
            self.on_press,
        )
        self.canvas.mpl_connect(
            "motion_notify_event",
            self.on_motion,
        )
        self.canvas.mpl_connect(
            "button_release_event",
            self.on_release,
        )
        self.canvas.mpl_connect(
            "scroll_event",
            self.on_scroll,
        )

        toolbar_frame = tk.Frame(main, bg="#10141D")
        toolbar_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.toolbar = NavigationToolbar2Tk(
            self.canvas,
            toolbar_frame,
            pack_toolbar=False,
        )
        self.toolbar.update()
        self.toolbar.pack(side="left")

        controls = tk.Frame(main, bg="#171D29")
        controls.pack(fill="x", padx=12, pady=(0, 12))

        tk.Button(
            controls,
            text="RESET VIEW",
            command=self.reset_view,
            bg="#263344",
            fg="#72E0CB",
            activebackground="#34465B",
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Consolas", 10, "bold"),
            padx=14,
            pady=8,
        ).pack(side="left", padx=10, pady=8)

        self.status_label = tk.Label(
            controls,
            text="",
            bg="#171D29",
            fg="#91A0B5",
            anchor="w",
            font=("Consolas", 9),
        )
        self.status_label.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10,
        )

    def update_amino_acids(self, event=None):
        items = AMINO_ACIDS[self.category.get()]
        names = [
            f"{name} ({code})"
            for name, code, smiles in items
        ]

        self.amino_box["values"] = names
        self.count_label.config(
            text=f"{len(items):02d} AMINO ACIDS"
        )

        if names:
            self.amino_box.current(0)
            self.select_amino()

    def select_amino(self, event=None):
        selection = self.selected.get()
        if not selection:
            return

        entry = next(
            (
                item
                for item in AMINO_ACIDS[self.category.get()]
                if f"{item[0]} ({item[1]})" == selection
            ),
            None,
        )

        if entry is None:
            return

        name, code, smiles = entry
        mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            messagebox.showerror(
                "Structure Error",
                f"Could not parse the structure of {name}.",
            )
            return

        mol = Chem.AddHs(mol)

        params = AllChem.ETKDGv3()
        params.randomSeed = 42

        result = AllChem.EmbedMolecule(mol, params)

        if result != 0:
            messagebox.showerror(
                "3D Generation Error",
                f"Could not generate a 3D structure for {name}.",
            )
            return

        if AllChem.MMFFHasAllMoleculeParams(mol):
            AllChem.MMFFOptimizeMolecule(
                mol,
                maxIters=500,
            )
        else:
            AllChem.UFFOptimizeMolecule(
                mol,
                maxIters=500,
            )

        conformer = mol.GetConformer()
        coords = np.array([
            list(conformer.GetAtomPosition(i))
            for i in range(mol.GetNumAtoms())
        ])

        self.mol = mol
        self.coords = coords
        self.view_elev = 22
        self.view_azim = 35
        self.zoom = 1.0

        self.name_label.config(text=name)
        self.info_label.config(
            text=f"{code.upper()}  /  {self.category.get().upper()}"
        )

        self.draw_molecule()

    def draw_bond(self, start, end, order):
        vector = end - start

        if np.linalg.norm(vector) < 1e-10:
            return

        direction = vector / np.linalg.norm(vector)
        reference = np.array([0.0, 0.0, 1.0])
        perpendicular = np.cross(direction, reference)

        if np.linalg.norm(perpendicular) < 1e-6:
            reference = np.array([0.0, 1.0, 0.0])
            perpendicular = np.cross(direction, reference)

        perpendicular /= np.linalg.norm(perpendicular)
        offset = 0.065

        if order == 1:
            shifts = [0]
        elif order == 2:
            shifts = [-offset, offset]
        elif order == 3:
            shifts = [-offset, 0, offset]
        else:
            shifts = [0]

        for shift in shifts:
            p1 = start + perpendicular * shift
            p2 = end + perpendicular * shift

            self.ax.plot(
                [p1[0], p2[0]],
                [p1[1], p2[1]],
                [p1[2], p2[2]],
                color="#8996A9",
                linewidth=1.8,
                alpha=0.95,
            )

    def draw_molecule(self):
        if self.mol is None or self.coords is None:
            return

        self.ax.clear()
        self.ax.set_facecolor("#10141D")
        self.ax.set_axis_off()

        visible = set()

        for atom in self.mol.GetAtoms():
            if self.show_hydrogens.get() or atom.GetSymbol() != "H":
                visible.add(atom.GetIdx())

        for bond in self.mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()

            if i not in visible or j not in visible:
                continue

            order = int(round(bond.GetBondTypeAsDouble()))

            self.draw_bond(
                self.coords[i],
                self.coords[j],
                order,
            )

        for atom in self.mol.GetAtoms():
            i = atom.GetIdx()

            if i not in visible:
                continue

            element = atom.GetSymbol()
            x, y, z = self.coords[i]

            self.ax.scatter(
                x, y, z,
                s=ATOM_SIZES.get(element, 150),
                c=[ATOM_COLORS.get(element, "#FFFFFF")],
                edgecolors="#E6EBF2",
                linewidths=0.65,
                depthshade=True,
            )

            if self.show_labels.get():
                label = element
                charge = atom.GetFormalCharge()

                if charge > 0:
                    label += "+" if charge == 1 else f"+{charge}"
                elif charge < 0:
                    label += "-" if charge == -1 else str(charge)

                if element != "C" or charge != 0:
                    self.ax.text(
                        x, y, z,
                        label,
                        color="#FFFFFF",
                        fontsize=8,
                        ha="center",
                        va="center",
                    )

        coords = self.coords[list(visible)]
        mins = coords.min(axis=0)
        maxs = coords.max(axis=0)
        center = (mins + maxs) / 2

        radius = max(
            float(np.max(maxs - mins)) / 2,
            1.0,
        ) * 1.3 / self.zoom

        self.ax.set_xlim(
            center[0] - radius,
            center[0] + radius,
        )
        self.ax.set_ylim(
            center[1] - radius,
            center[1] + radius,
        )
        self.ax.set_zlim(
            center[2] - radius,
            center[2] + radius,
        )

        self.ax.set_box_aspect((1, 1, 1))
        self.ax.view_init(
            elev=self.view_elev,
            azim=self.view_azim,
        )

        heavy_atoms = sum(
            atom.GetSymbol() != "H"
            for atom in self.mol.GetAtoms()
        )
        hydrogen_atoms = self.mol.GetNumAtoms() - heavy_atoms
        net_charge = sum(
            atom.GetFormalCharge()
            for atom in self.mol.GetAtoms()
        )

        self.status_label.config(
            text=(
                f"ATOMS {heavy_atoms} HEAVY / {hydrogen_atoms} H"
                f"    BONDS {self.mol.GetNumBonds()}"
                f"    NET CHARGE {net_charge:+d}"
            )
        )

        self.canvas.draw_idle()

    def on_press(self, event):
        if event.inaxes != self.ax:
            return

        if event.button == 1:
            self.dragging = True
            self.last_mouse = (event.x, event.y)

    def on_motion(self, event):
        if not self.dragging or self.last_mouse is None:
            return

        if event.x is None or event.y is None:
            return

        dx = event.x - self.last_mouse[0]
        dy = event.y - self.last_mouse[1]

        self.view_azim += dx * 0.6
        self.view_elev = max(
            -90,
            min(90, self.view_elev + dy * 0.6),
        )

        self.last_mouse = (event.x, event.y)
        self.ax.view_init(
            elev=self.view_elev,
            azim=self.view_azim,
        )
        self.canvas.draw_idle()

    def on_release(self, event):
        self.dragging = False
        self.last_mouse = None

    def on_scroll(self, event):
        if event.button == "up":
            self.zoom = min(3.0, self.zoom * 1.12)
        else:
            self.zoom = max(0.35, self.zoom / 1.12)

        self.draw_molecule()

    def reset_view(self):
        self.view_elev = 22
        self.view_azim = 35
        self.zoom = 1.0
        self.draw_molecule()


if __name__ == "__main__":
    root = tk.Tk()
    app = AminoAcidViewer(root)
    root.mainloop()
