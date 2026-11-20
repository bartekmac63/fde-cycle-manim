from manim import *

config.pixel_height = 1080
config.pixel_width = 1920
config.frame_rate = 60
config.background_color = WHITE

ACCENT = "#B91C1C"
Text.set_default(font="Arial", color=BLACK)


class FDE(Scene):
    def construct(self):
        self.regs = {}
        self.reg_txts = {}
        self.ram_cells = {}
        self.stack_boxes = []
        self.stack_txts = []
        self.sp = 0

        self.setup_layout()
        self.cycle_one()
        self.cycle_two_interrupt()
        self.handle_isr()
        self.wait(2)

    def reg_row(self, label, val):
        left = Rectangle(width=1.0, height=0.72, fill_color=BLACK, fill_opacity=1, stroke_color=BLACK)
        l_txt = Text(label, font_size=17, weight=BOLD, color=WHITE)

        right = Rectangle(width=1.95, height=0.72, fill_color=WHITE, fill_opacity=1, stroke_color=BLACK, stroke_width=2)
        r_txt = Text(val, font_size=18, weight=BOLD)

        self.regs[label] = right
        self.reg_txts[label] = r_txt

        row = VGroup(left, right).arrange(RIGHT, buff=0)
        l_txt.move_to(left)
        r_txt.move_to(right)
        return VGroup(row, l_txt, r_txt)

    def token(self, text, fill=ACCENT):
        t = Text(str(text), font_size=14, weight=BOLD, color=WHITE)
        box = RoundedRectangle(
            corner_radius=0.06,
            width=max(t.width + 0.3, 0.8),
            height=0.36,
            fill_color=fill,
            fill_opacity=1,
            stroke_color=BLACK,
            stroke_width=1.5,
        )
        t.move_to(box)
        return VGroup(box, t)

    def setup_layout(self):
        # top bar + bottom caption
        self.header = Text("Fetch-Decode-Execute & Interrupt Cycle", font_size=24, weight=BOLD).to_edge(UP, buff=0.25)
        self.sub_header = Text(
            "PC = 0100 | ACC = 0005 | SR = OK | IR = None", font_size=17, weight=BOLD, color=ACCENT
        ).next_to(self.header, DOWN, buff=0.12)
        self.caption_box = Rectangle(width=13.2, height=0.68, fill_color=WHITE, fill_opacity=1, stroke_color=BLACK, stroke_width=1.8).to_edge(DOWN, buff=0.22)
        self.divider = Line(LEFT, RIGHT, color=BLACK, stroke_width=1.5).set(
            width=self.caption_box.width
        ).next_to(self.sub_header, DOWN, buff=0.12)
        self.caption = Text(
            "Von Neumann Architecture: instructions and data share Main Memory.", font_size=17
        ).move_to(self.caption_box)

        self.add(self.header, self.sub_header, self.divider, self.caption_box, self.caption)

        # left side: CPU
        self.cpu_box = Rectangle(width=5.6, height=5.8, stroke_color=BLACK, stroke_width=2.2).to_edge(
            LEFT, buff=0.45
        ).align_to(self.divider, UP)
        cpu_title = Text("CPU", font_size=20, weight=BOLD, color=ACCENT).next_to(self.cpu_box.get_top(), DOWN, buff=0.18)

        reg_group = VGroup(
            self.reg_row("PC", "0100"),
            self.reg_row("MAR", "------"),
            self.reg_row("MBR", "------"),
            self.reg_row("CIR", "------"),
            self.reg_row("ACC", "0005"),
        ).arrange(DOWN, buff=0.28).next_to(cpu_title, DOWN, buff=0.28).align_to(self.cpu_box, LEFT).shift(RIGHT * 0.2)

        # CU, ALU, status flags
        self.cu_box = Rectangle(width=2.15, height=1.95, stroke_color=BLACK, stroke_width=2).next_to(reg_group, RIGHT, buff=0.22).align_to(reg_group, UP)
        cu_title = Text("Control Unit", font_size=16, weight=BOLD).next_to(self.cu_box.get_top(), DOWN, buff=0.14)
        clk_txt = Text("Clock: Active", font_size=13, color=ACCENT).next_to(cu_title, DOWN, buff=0.12)

        self.dec_box = Rectangle(width=1.9, height=0.95, stroke_color=BLACK, stroke_width=1.5).next_to(clk_txt, DOWN, buff=0.14)
        dec_lbl = Text("Decoder", font_size=14, weight=BOLD).next_to(self.dec_box.get_top(), DOWN, buff=0.1)
        self.dec_status = Text("Idle", font_size=13, weight=BOLD, color=ACCENT).next_to(dec_lbl, DOWN, buff=0.12)

        self.alu_box = Rectangle(width=2.15, height=1.25, stroke_color=BLACK, stroke_width=2).next_to(self.cu_box, DOWN, buff=0.2)
        alu_title = Text("ALU", font_size=16, weight=BOLD).next_to(self.alu_box.get_top(), DOWN, buff=0.14)
        self.alu_status = Text("Ready", font_size=13).next_to(alu_title, DOWN, buff=0.14)

        flags_box = Rectangle(width=2.15, height=1.25, stroke_color=BLACK, stroke_width=2).next_to(self.alu_box, DOWN, buff=0.2)
        self.sr_box = Rectangle(width=1.15, height=0.42, stroke_color=BLACK, stroke_width=1.5)
        self.sr_txt = Text("OK", font_size=13, weight=BOLD).move_to(self.sr_box)
        sr_lbl = Text("SR:", font_size=14, weight=BOLD)
        sr_value = VGroup(self.sr_box, self.sr_txt)
        sr_row = VGroup(sr_lbl, sr_value).arrange(RIGHT, buff=0.12)

        self.ir_box = Rectangle(width=1.15, height=0.42, stroke_color=BLACK, stroke_width=1.5)
        self.ir_txt = Text("None", font_size=13, weight=BOLD).move_to(self.ir_box)
        ir_lbl = Text("IR:", font_size=14, weight=BOLD)
        ir_value = VGroup(self.ir_box, self.ir_txt)
        ir_row = VGroup(ir_lbl, ir_value).arrange(RIGHT, buff=0.12)
        flag_rows = VGroup(sr_row, ir_row).arrange(DOWN, buff=0.14).move_to(flags_box)

        self.add(
            self.cpu_box, cpu_title, reg_group,
            self.cu_box, cu_title, clk_txt, self.dec_box, dec_lbl, self.dec_status,
            self.alu_box, alu_title, self.alu_status,
            flags_box, flag_rows,
        )

        # right side: RAM + stack
        self.ram_box = Rectangle(width=4.8, height=3.35, stroke_color=BLACK, stroke_width=2.2).to_edge(RIGHT, buff=0.45).align_to(self.cpu_box, UP)
        ram_title = Text("Main Memory", font_size=20, weight=BOLD, color=ACCENT).next_to(self.ram_box.get_top(), DOWN, buff=0.18)

        mem_data = [("0100", "ADD 0105"), ("0101", "SUB 0106"), ("0105", "0012"), ("0106", "0002")]
        mem_rows = VGroup()
        for addr, val in mem_data:
            a_cell = Rectangle(width=1.1, height=0.46, fill_color=BLACK, fill_opacity=1, stroke_color=BLACK)
            a_txt = Text(addr, font_size=15, weight=BOLD, color=WHITE).move_to(a_cell)
            a_grp = VGroup(a_cell, a_txt)

            v_cell = Rectangle(width=3.2, height=0.46, fill_color=WHITE, fill_opacity=1, stroke_color=BLACK, stroke_width=1.6)
            v_txt = Text(val, font_size=15, weight=BOLD, color=BLACK).move_to(v_cell)
            v_grp = VGroup(v_cell, v_txt)

            self.ram_cells[addr] = v_cell
            row = VGroup(a_grp, v_grp).arrange(RIGHT, buff=0)
            mem_rows.add(row)

        mem_rows.arrange(DOWN, buff=0.12).next_to(ram_title, DOWN, buff=0.22)

        self.stack_box = Rectangle(width=4.8, height=2.25, stroke_color=BLACK, stroke_width=2.2).next_to(self.ram_box, DOWN, buff=0.2).align_to(self.ram_box, LEFT)
        stack_title = Text("System Stack", font_size=18, weight=BOLD).next_to(self.stack_box.get_top(), DOWN, buff=0.14)

        slots = VGroup()
        for _ in range(3):
            s_box = Rectangle(width=3.8, height=0.44, stroke_color=BLACK, stroke_width=1.5)
            s_txt = Text("[ empty ]", font_size=14).move_to(s_box)
            self.stack_boxes.append(s_box)
            self.stack_txts.append(s_txt)
            slots.add(VGroup(s_box, s_txt))

        slots.arrange(UP, buff=0.1).next_to(stack_title, DOWN, buff=0.16)
        self.add(self.ram_box, ram_title, mem_rows, self.stack_box, stack_title, slots)

        # buses in the middle
        bus_gap = self.ram_box.get_left()[0] - self.cpu_box.get_right()[0]
        bus_width = bus_gap - 0.2
        self.addr_bus = Arrow(LEFT, RIGHT, buff=0, color=ACCENT, stroke_width=4).set(width=bus_width)
        self.data_bus = DoubleArrow(
            LEFT, RIGHT, buff=0, color=BLACK, stroke_width=4, tip_length=0.2
        ).set(width=bus_width)
        self.ctrl_bus = DoubleArrow(
            LEFT, RIGHT, buff=0, color=ACCENT, stroke_width=4, tip_length=0.2
        ).set(width=bus_width)
        buses = VGroup(self.addr_bus, self.data_bus, self.ctrl_bus).arrange(DOWN, buff=1.4)
        bus_center = (self.cpu_box.get_right() + self.ram_box.get_left()) / 2
        bus_center[1] = (self.divider.get_bottom()[1] + self.caption_box.get_top()[1]) / 2
        buses.move_to(bus_center)

        self.add(
            self.addr_bus, Text("Address Bus", font_size=14, weight=BOLD, color=ACCENT).next_to(self.addr_bus, UP, buff=0.1),
            self.data_bus, Text("Data Bus", font_size=14, weight=BOLD).next_to(self.data_bus, UP, buff=0.1),
            self.ctrl_bus, Text("Control Bus", font_size=14, weight=BOLD, color=ACCENT).next_to(self.ctrl_bus, UP, buff=0.1),
        )

    def update_hud(self, title, status, desc):
        t1 = Text(title, font_size=24, weight=BOLD).move_to(self.header)
        t2 = Text(status, font_size=17, weight=BOLD, color=ACCENT).move_to(self.sub_header)
        t3 = Text(desc, font_size=16).move_to(self.caption_box)
        self.play(
            FadeTransform(self.header, t1),
            FadeTransform(self.sub_header, t2),
            FadeTransform(self.caption, t3),
            run_time=0.45,
        )
        self.header, self.sub_header, self.caption = t1, t2, t3

    def write_reg(self, reg, val, col=BLACK):
        box = self.regs[reg]
        lbl = Text(val, font_size=18, weight=BOLD, color=col).move_to(box)
        self.play(FadeTransform(self.reg_txts[reg], lbl), Indicate(box, color=ACCENT, scale_factor=1.05), run_time=0.4)
        self.reg_txts[reg] = lbl

    def move_packet(self, p0, p1, label, col=ACCENT, t=0.6):
        pkt = self.token(label, col).move_to(p0)
        self.play(FadeIn(pkt, scale=0.9), run_time=0.12)
        self.play(pkt.animate.move_to(p1), run_time=t)
        self.play(FadeOut(pkt, scale=0.9), run_time=0.12)

    def bus_transfer(self, bus, label, to_ram=True, col=ACCENT):
        p0, p1 = (bus.get_start(), bus.get_end()) if to_ram else (bus.get_end(), bus.get_start())
        pkt = self.token(label, col).next_to(bus, DOWN, buff=0.17).set_x(p0[0])
        self.play(FadeIn(pkt), bus.animate.set_stroke(width=6.5), run_time=0.18)
        self.play(pkt.animate.set_x(p1[0]), run_time=0.7)
        self.play(FadeOut(pkt), bus.animate.set_stroke(width=4), run_time=0.18)

    def push(self, label, src, col=ACCENT):
        box = self.stack_boxes[self.sp]
        self.move_packet(src, box.get_center(), label, col, t=0.5)
        txt = Text(label, font_size=15, weight=BOLD, color=ACCENT).move_to(box)
        self.play(FadeTransform(self.stack_txts[self.sp], txt), box.animate.set_stroke(ACCENT, width=2.2), run_time=0.25)
        self.stack_txts[self.sp] = txt
        self.sp += 1

    def pop(self, dst, col=BLACK):
        self.sp -= 1
        box = self.stack_boxes[self.sp]
        val = self.stack_txts[self.sp].text
        blank = Text("[ empty ]", font_size=14).move_to(box)
        self.play(FadeTransform(self.stack_txts[self.sp], blank), box.animate.set_stroke(BLACK, width=1.5), run_time=0.25)
        self.stack_txts[self.sp] = blank
        self.move_packet(box.get_center(), dst, val, col, t=0.5)

    def cycle_one(self):
        self.wait(1.2)

        # 1. PC -> MAR
        self.update_hud(
            "1. Fetch: Copy PC to MAR",
            "MAR <- [PC]",
            "Copy the next instruction address (0100) from PC into MAR.",
        )
        self.move_packet(self.regs["PC"].get_center(), self.regs["MAR"].get_center(), "0100")
        self.write_reg("MAR", "0100", ACCENT)
        self.wait(0.6)

        # 2. lookup + increment PC
        self.update_hud(
            "2. Fetch: Address Lookup & Increment PC",
            "PC <- [PC] + 1  |  Address Bus: 0100",
            "Send 0100 over the Address Bus to read RAM while incrementing PC to 0101.",
        )
        self.bus_transfer(self.addr_bus, "0100", to_ram=True, col=ACCENT)
        self.write_reg("PC", "0101", ACCENT)
        self.play(Indicate(self.ram_cells["0100"], color=ACCENT), run_time=0.45)

        # 3. RAM -> MBR -> CIR
        self.update_hud(
            "3. Fetch: Load Instruction into MBR & CIR",
            "MBR <- [RAM]  |  CIR <- [MBR]",
            "ADD 0105 comes back on the Data Bus into MBR, then moves to CIR.",
        )
        self.bus_transfer(self.data_bus, "ADD 0105", to_ram=False, col=BLACK)
        self.write_reg("MBR", "ADD 0105")
        self.move_packet(self.regs["MBR"].get_center(), self.regs["CIR"].get_center(), "ADD 0105", BLACK)
        self.write_reg("CIR", "ADD 0105")
        self.wait(0.6)

        # 4. decode
        self.update_hud(
            "4. Decode: Split Opcode and Operand",
            "Opcode: ADD  |  Operand: 0105",
            "The Control Unit splits ADD 0105 into the operation (ADD) and address (0105).",
        )
        self.move_packet(self.regs["CIR"].get_center(), self.dec_box.get_center(), "ADD 0105")
        dec = Text("ADD | 0105", font_size=14, weight=BOLD, color=ACCENT).move_to(self.dec_status)
        self.play(FadeTransform(self.dec_status, dec), Indicate(self.dec_box, color=ACCENT), run_time=0.4)
        self.dec_status = dec
        self.wait(0.6)

        # 5. execute
        self.update_hud(
            "5. Execute: Fetch Operand & Add",
            "ACC <- [ACC] + [0105]  (0005 + 0012 = 0017)",
            "Fetch the value at 0105 into MBR (0012) and add it to ACC in the ALU.",
        )
        self.move_packet(self.regs["CIR"].get_center(), self.regs["MAR"].get_center(), "0105")
        self.write_reg("MAR", "0105", ACCENT)
        self.bus_transfer(self.addr_bus, "0105", to_ram=True, col=ACCENT)
        self.bus_transfer(self.data_bus, "0012", to_ram=False, col=BLACK)
        self.write_reg("MBR", "0012")

        alu = Text("0005 + 0012 = 0017", font_size=13, weight=BOLD, color=ACCENT).move_to(self.alu_status)
        self.play(FadeTransform(self.alu_status, alu), Indicate(self.alu_box, color=ACCENT), run_time=0.45)
        self.alu_status = alu
        self.move_packet(self.alu_box.get_center(), self.regs["ACC"].get_center(), "0017")
        self.write_reg("ACC", "0017", ACCENT)
        self.wait(0.6)

        # 6. check interrupts
        self.update_hud(
            "6. Check Interrupt Register",
            "IR = None -> Continue",
            "End of cycle: check IR for pending interrupts. Nothing queued.",
        )
        self.play(Indicate(self.ir_box, color=ACCENT), run_time=0.5)
        self.wait(0.5)

    def cycle_two_interrupt(self):
        self.update_hud(
            "7. Next Cycle (SUB 0106) & Hardware Interrupt",
            "ACC <- 0017 - 0002 = 0015  |  Keypress -> IR",
            "During SUB 0106, a keyboard signal arrives on the Control Bus and flags IR.",
        )
        self.write_reg("MAR", "0101", ACCENT)
        self.write_reg("PC", "0102")
        self.bus_transfer(self.data_bus, "SUB 0106", to_ram=False, col=BLACK)
        self.write_reg("MBR", "SUB 0106")
        self.write_reg("CIR", "SUB 0106")

        self.write_reg("MAR", "0106", ACCENT)
        self.bus_transfer(self.data_bus, "0002", to_ram=False, col=BLACK)
        self.write_reg("MBR", "0002")

        alu = Text("0017 - 0002 = 0015", font_size=13, weight=BOLD, color=ACCENT).move_to(self.alu_status)
        self.play(FadeTransform(self.alu_status, alu), run_time=0.35)
        self.alu_status = alu
        self.write_reg("ACC", "0015", ACCENT)

        # interrupt hits
        self.bus_transfer(self.ctrl_bus, "Keypress", to_ram=False, col=ACCENT)
        ir = Text("Keyboard", font_size=13, weight=BOLD, color=ACCENT).move_to(self.ir_box)
        self.play(FadeTransform(self.ir_txt, ir), self.ir_box.animate.set_stroke(ACCENT, width=2.2), run_time=0.35)
        self.ir_txt = ir
        self.wait(0.6)

    def handle_isr(self):
        # save context
        self.update_hud(
            "8. Interrupt Detected: Save State to Stack",
            "Push PC, CIR, SR onto System Stack",
            "Save current register state onto the stack before jumping to the ISR.",
        )
        self.push("PC: 0102", self.regs["PC"].get_center(), BLACK)
        self.push("CIR: SUB 0106", self.regs["CIR"].get_center(), ACCENT)
        self.push("SR: OK", self.sr_box.get_center(), BLACK)
        self.wait(0.6)

        # jump to ISR
        self.update_hud(
            "9. Run Interrupt Service Routine (ISR)",
            "Jump to ISR (0900) -> Clear IR",
            "Load ISR vector into PC/CIR, handle the keypress, and reset IR.",
        )
        self.write_reg("PC", "0900", ACCENT)
        self.write_reg("CIR", "ISR_KEY", ACCENT)

        dec = Text("Running ISR", font_size=13, weight=BOLD, color=ACCENT).move_to(self.dec_status)
        self.play(FadeTransform(self.dec_status, dec), Indicate(self.cu_box, color=ACCENT), run_time=0.45)
        self.dec_status = dec

        ir_clear = Text("None", font_size=13, weight=BOLD).move_to(self.ir_box)
        self.play(FadeTransform(self.ir_txt, ir_clear), self.ir_box.animate.set_stroke(BLACK, width=1.5), run_time=0.35)
        self.ir_txt = ir_clear
        self.wait(0.6)

        # restore context (LIFO)
        self.update_hud(
            "10. Restore State (LIFO) & Resume",
            "Pop SR, CIR, PC -> Resume at 0102",
            "Pop saved values off the stack in reverse order and continue from 0102.",
        )
        self.pop(self.sr_box.get_center(), BLACK)
        self.pop(self.regs["CIR"].get_center(), ACCENT)
        self.write_reg("CIR", "SUB 0106")
        self.pop(self.regs["PC"].get_center(), BLACK)
        self.write_reg("PC", "0102", ACCENT)