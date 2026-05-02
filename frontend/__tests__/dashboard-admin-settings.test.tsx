import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import SuperAdminPage from "@/app/super-admin/page";
import { api } from "@/lib/api";

const pushMock = jest.fn();
const replaceMock = jest.fn();
const routerMock = {
  push: pushMock,
  replace: replaceMock,
};

jest.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

jest.mock("@/store/authStore", () => ({
  useAuthStore: () => ({
    initializeAuth: jest.fn(),
    user: {
      id: "admin-id",
      first_name: "Super",
      last_name: "Admin",
      username: "admin",
      email: "admin@aexiz.com",
      company_name: "Eureka",
      phone_number: null,
      role: "admin",
      subscription_tier: "admin",
      approval_status: "approved",
      created_at: "2026-04-25T00:00:00Z",
    },
    logout: jest.fn(),
  }),
}));

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
    patch: jest.fn(),
  },
}));

describe("Super admin page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.get as jest.Mock).mockImplementation((url: string) => {
      if (url.startsWith("/api/v1/admin/onboarding/requests")) {
        return Promise.resolve({
          data: {
            data: [
              {
                id: "user-id",
                first_name: "Aman",
                last_name: "Kumar",
                username: "store_user",
                email: "user@example.com",
                company_name: "Brand11",
                phone_number: "1234567890",
                role: "merchandiser",
                subscription_tier: "individual-plus",
                approval_status: "pending",
                reviewed_at: null,
                review_note: null,
                created_at: "2026-05-01T10:00:00Z",
                layout_count: 3,
                plan_limit: {
                  annual_planogram_limit: 15,
                  is_unlimited: false,
                  source: "tier",
                },
              },
            ],
            message: "ok",
          },
        });
      }

      if (url === "/api/v1/admin/users") {
        return Promise.resolve({
          data: {
            data: [
              {
                id: "user-id",
                first_name: "Aman",
                last_name: "Kumar",
                username: "store_user",
                email: "user@example.com",
                company_name: "Brand11",
                phone_number: "1234567890",
                role: "merchandiser",
                subscription_tier: "individual-plus",
                approval_status: "approved",
                reviewed_at: "2026-05-01T12:00:00Z",
                review_note: "approved",
                created_at: "2026-05-01T10:00:00Z",
                layout_count: 3,
                plan_limit: {
                  annual_planogram_limit: 15,
                  is_unlimited: false,
                  source: "tier",
                },
              },
            ],
            message: "ok",
          },
        });
      }

      return Promise.resolve({
        data: {
          data: [
            { tier: "individual-plus", annual_planogram_limit: 15, is_unlimited: false },
            { tier: "individual-pro", annual_planogram_limit: 45, is_unlimited: false },
          ],
          message: "ok",
        },
      });
    });

    (api.patch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes("/plan-limit")) {
        return Promise.resolve({
          data: {
            data: {
              user_id: "user-id",
              plan_limit: {
                annual_planogram_limit: 20,
                is_unlimited: false,
                source: "override",
              },
            },
            message: "saved",
          },
        });
      }

      return Promise.resolve({
        data: {
          data: { status: "approved" },
          message: "saved",
        },
      });
    });
  });

  it("renders onboarding table and can approve a request", async () => {
    render(<SuperAdminPage />);

    expect(await screen.findByText("Super Admin · Pilot Onboarding")).toBeInTheDocument();
    expect(await screen.findByText(/store_user/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Approve" }));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith("/api/v1/admin/onboarding/requests/user-id", expect.any(Object)));
  });

  it("renders limits tab and updates per-user limits", async () => {
    render(<SuperAdminPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Limits" }));

    fireEvent.click(await screen.findByRole("button", { name: "Edit limits for store_user" }));
    fireEvent.click(await screen.findByLabelText("Use Individual Plus tier default"));

    const input = await screen.findByLabelText("Annual planogram limit");
    fireEvent.change(input, { target: { value: "20" } });
    fireEvent.click(screen.getByRole("button", { name: "Save limits" }));

    await waitFor(() =>
      expect(api.patch).toHaveBeenCalledWith("/api/v1/admin/users/user-id/plan-limit", {
        annual_planogram_limit: 20,
        is_unlimited: false,
      }),
    );
  });
});
