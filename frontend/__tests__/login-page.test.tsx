import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import LoginPage from "@/app/(auth)/login/page";

const pushMock = jest.fn();
const replaceMock = jest.fn();
const loginMock = jest.fn().mockResolvedValue(undefined);
const initializeAuthMock = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    replace: replaceMock,
  }),
}));

jest.mock("@/store/authStore", () => ({
  useAuthStore: () => ({
    login: loginMock,
    token: null,
    initializeAuth: initializeAuthMock,
  }),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("signs in with email and password", async () => {
    const user = userEvent.setup();

    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => expect(loginMock).toHaveBeenCalledWith("user@example.com", "password123"));
    expect(initializeAuthMock).toHaveBeenCalled();
  });
});