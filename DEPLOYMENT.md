# Chanjo2 - Deployment

> **Note**  
> These instructions apply **only** for deployments at Clinical Genomics, SciLifeLab Stockholm.  
> If you need generic deployment instructions for Chanjo2, please consult the official guide.

1. [ Testing a branch on cg-vm1 (stage) ](#cg-vm1-stage)
1. [ Deploying a new release on cg-prod-services (prod) ](#cg-prod)

---

<a name="cg-vm1-stage"></a>

## Testing a branch on cg-vm1 (stage)

1. Make sure the branch you want to test has been pushed and is available on [Docker Hub](https://hub.docker.com/repository/docker/clinicalgenomics/chanjo2-stage).
2. Book your testing slot using [Paxa](https://pax.scilifelab.se/), specifying:
   - **Resource:** `chanjo2`
   - **Server:** `cg-services-stage`
3. Log into the server:

   ```shell
   ssh <USER.NAME>@cg-vm1.scilifelab.se
   sudo -iu hiseq.clinical
   ssh localhost
   ```

4. (Optional) Check which branch is currently deployed:

   ```shell
   podman ps
   ```

5. Stop the currently running service:

   ```shell
   systemctl --user stop chanjo2.target
   ```

6. Start Chanjo2 with the branch you want to test:

   ```shell
   systemctl --user start chanjo2@<branch_to_test>
   ```

7. Confirm the branch is active:

   ```shell
   systemctl --user status chanjo2.target
   ```

8. After testing, ensure no failed services remain:

   ```shell
   systemctl --user list-dependencies chanjo2.target
   systemctl --user reset-failed chanjo2@<branch_with_failed_state>
   ```

9. Release the booked resource in Paxa so other users can test.

---

<a name="cg-prod"></a>

## Deploying a new release on cg-prod-services (prod)

1. Make sure the release is available on [Docker Hub](https://hub.docker.com/repository/docker/clinicalgenomics/chanjo2).
2. Log into the server:

   ```shell
   ssh <USER.NAME>@cg-prod-services.scilifelab.se
   sudo -iu hiseq.clinical
   ssh localhost
   ```

3. Stop the currently running service:

   ```shell
   systemctl --user stop chanjo2.target
   ```

4. Start Chanjo2 with the release version:

   ```shell
   systemctl --user start chanjo2@<release_version>
   ```

5. Confirm the release is running:

   ```shell
   systemctl --user status chanjo2.target
   ```

6. Verify in the [production web interface](https://chanjo2.scilifelab.se/) that the correct version is deployed.
7. Optionally, clean up failed services:

   ```shell
   systemctl --user list-dependencies chanjo2.target
   systemctl --user reset-failed chanjo2@my_release_with_failed_state
   ```

---