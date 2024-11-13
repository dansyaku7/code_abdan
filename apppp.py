import wx
import cv2
import numpy as np
import threading

class ReceiptPrintout(wx.Printout):
    def __init__(self, content):
        super(ReceiptPrintout, self).__init__()
        self.content = content

    def OnPrintPage(self, page):
        # Draw the content of the receipt on the printout page
        dc = self.GetDC()
        
        # Set a larger font size (e.g., 18)
        dc.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Draw the text at the specified position (100, 100)
        dc.DrawText(self.content, 100, 100)

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        super(MainWindow, self).__init__(parent, title=title, size=(400, 400))
        
        # Initialize GUI components
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Inputs for Name, Plate Number, Vehicle Type, Brand, and Opacity
        self.name_label = wx.StaticText(self.panel, label="Name:")
        self.vbox.Add(self.name_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        self.name_input = wx.TextCtrl(self.panel)
        self.vbox.Add(self.name_input, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        
        self.plate_label = wx.StaticText(self.panel, label="Plate Number:")
        self.vbox.Add(self.plate_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        
        self.plate_input = wx.TextCtrl(self.panel)
        self.vbox.Add(self.plate_input, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        self.vehicle_type_label = wx.StaticText(self.panel, label="Vehicle Type:")
        self.vbox.Add(self.vehicle_type_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.vehicle_type_input = wx.TextCtrl(self.panel)
        self.vbox.Add(self.vehicle_type_input, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        self.brand_label = wx.StaticText(self.panel, label="Vehicle Brand:")
        self.vbox.Add(self.brand_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.brand_input = wx.TextCtrl(self.panel)
        self.vbox.Add(self.brand_input, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        self.opacity_label = wx.StaticText(self.panel, label="Opacity (%):")
        self.vbox.Add(self.opacity_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.opacity_input = wx.TextCtrl(self.panel)
        self.vbox.Add(self.opacity_input, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # Print Button
        self.print_button = wx.Button(self.panel, label="Print")
        self.print_button.Bind(wx.EVT_BUTTON, self.on_print)
        self.vbox.Add(self.print_button, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=20)

        # Camera Toggle Button
        self.toggle_camera_button = wx.Button(self.panel, label="Show Camera")
        self.toggle_camera_button.Bind(wx.EVT_BUTTON, self.toggle_camera)
        self.vbox.Add(self.toggle_camera_button, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=20)

        self.panel.SetSizer(self.vbox)
        self.Centre()

        # Initialize OpenCV video capture
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, -2)

        # Create a thread to run the camera feed and processing in parallel with the GUI
        self.camera_thread = threading.Thread(target=self.camera_loop)
        self.camera_thread.daemon = True
        self.camera_thread.start()

        self.show_camera = False  # Camera is hidden by default
        self.Show()

    def detect_black_color(self, frame):
        # Determine the center of the frame
        height, width, _ = frame.shape
        center_x, center_y = width // 2, height // 2
        
        # Define the center area for object detection
        center_area = frame[center_y-100:center_y+100, center_x-100:center_x+100]
        
        # Convert the frame to HSV color space
        hsv = cv2.cvtColor(center_area, cv2.COLOR_BGR2HSV)
        
        # Define the range for black color in HSV space
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 80])
        
        # Mask for detecting black in the defined range
        mask = cv2.inRange(hsv, lower_black, upper_black)
        
        # Count the number of black pixels and calculate the percentage
        black_pixels = np.count_nonzero(mask)
        total_pixels = mask.size
        darkness_percentage = (black_pixels / total_pixels) * 100
        
        return darkness_percentage

    def camera_loop(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Detect black color and calculate opacity percentage
            darkness_percentage = self.detect_black_color(frame)

            # Update the opacity input field in the GUI
            wx.CallAfter(self.update_opacity, darkness_percentage)

            # Draw the opacity on the frame
            if darkness_percentage > 0:
                cv2.putText(frame, f'Opacity: {darkness_percentage:.0f}%', (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(frame, 'Opacity: 0%', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Add a dot at the center of the frame
            height, width, _ = frame.shape
            center_x, center_y = width // 2, height // 2
            cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)  # Green dot with radius 5

            # Show the camera feed if the flag is set to True
            if self.show_camera:
                cv2.imshow('Camera Feed', frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Release the camera and close OpenCV windows
        self.cap.release()
        cv2.destroyAllWindows()

    def update_opacity(self, darkness_percentage):
        # Update the opacity field in the GUI with the calculated percentage
        self.opacity_input.SetValue(f"{darkness_percentage:.0f}")

    def toggle_camera(self, event):
        # Toggle the camera view on or off
        self.show_camera = not self.show_camera
        if self.show_camera:
            self.toggle_camera_button.SetLabel("Hide Camera")
        else:
            self.toggle_camera_button.SetLabel("Show Camera")

    def on_print(self, event):
        # Create formatted text content for the receipt
        name = self.name_input.GetValue()
        plate = self.plate_input.GetValue()
        vehicle_type = self.vehicle_type_input.GetValue()
        brand = self.brand_input.GetValue()
        opacity = self.opacity_input.GetValue()
        
        # Format text to be printed
        print_content = (
            f"Name: {name}\n"
            f"Plate: {plate}\n"
            f"Type: {vehicle_type}\n"
            f"Brand: {brand}\n"
            f"Opacity: {opacity}%\n"
        )

        # Create a printout object
        printout = ReceiptPrintout(print_content)

        # Set up printer
        printer = wx.Printer()
        if not printer.Print(self, printout, True):
            wx.MessageBox("Printing failed!", "Error", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("Printing succeeded!", "Info", wx.OK | wx.ICON_INFORMATION)
    
        printout.Destroy()  # Clean up the printout

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None, "Thermal Printer GUI")
    app.MainLoop()
